import re
import sqlite3

from core.config import DB_PATH  # noqa: F401  (하위 호환 re-export)
from core.db import get_db, read_only, transaction  # noqa: F401

# get_db() 는 core.db 구현을 사용한다.
# (PRAGMA foreign_keys / WAL / 절대경로가 모든 커넥션에 일괄 적용됨)


def _backfill_character_fields(cursor, conn):
    """기존 캐릭터의 prompt 에서 구조화 필드를 되살린다.

    prompt 는 고정 템플릿으로 생성돼 있어 파싱이 가능하다.
    파싱에 실패하면 안전한 기본값(20세)을 쓴다 — 0 으로 두면 미성년 취급이 된다.
    """
    cursor.execute("SELECT id, prompt, age, personality FROM characters")
    rows = cursor.fetchall()
    fixed = 0
    for row in rows:
        # ALTER TABLE 의 DEFAULT 20 때문에 age 만 보면 전부 '이미 채워짐' 으로 보인다.
        # personality 가 비어 있으면 아직 backfill 되지 않은 행이다.
        if (row["personality"] or "").strip():
            continue
        prompt = row["prompt"] or ""
        if not prompt.strip():
            continue

        # \s 는 줄바꿈까지 먹어서 다음 줄을 잘못 집는다 — 같은 줄로 한정한다
        m = re.search(r"-[ \t]*나이:[ \t]*(\d+)[ \t]*세", prompt)
        age = int(m.group(1)) if m else 20
        if age < 19:
            age = 20  # 과거에 등록된 미성년 설정은 성인 기본값으로 올린다

        m = re.search(r"-[ \t]*직업:[ \t]*([^\n]*)", prompt)
        job = m.group(1).strip() if m else ""

        m = re.search(r"성격 및 외모:\s*\n(.*?)(?:\n\n|좋아하는 것:)", prompt, re.S)
        personality = m.group(1).strip() if m else ""

        m = re.search(r"말투:\s*\n(.*?)(?:\n\n|시작 상황:|절대 규칙:)", prompt, re.S)
        speech = m.group(1).strip() if m else ""

        cursor.execute(
            "UPDATE characters SET age = ?, job = ?, personality = ?, speech_style = ? WHERE id = ?",
            (age, job, personality, speech, row["id"]),
        )
        fixed += 1
    if fixed:
        conn.commit()
        print(f"[migrate] 캐릭터 구조화 필드 backfill: {fixed}건")


def _repair_dangling_fk_references(cursor, conn):
    """`*_old` 를 가리키는 깨진 FK 를 복구한다.

    _migrate_party_rooms_nullable 이 `ALTER TABLE party_rooms RENAME TO party_rooms_old`
    를 실행했는데, SQLite 3.25+ 는 이때 **자식 테이블의 FK 참조명까지 같이 바꾼다**.
    그래서 party_members 의 FK 가 party_rooms_old 를 가리킨 채로 남았고,
    그 테이블은 곧바로 DROP 됐다.

    지금까지는 PRAGMA foreign_keys 가 꺼져 있어 드러나지 않았지만, FK 를 켜는 순간
    party_members INSERT 가 전부 `no such table: main.party_rooms_old` 로 실패한다
    (= 방 만들기/입장 전멸). 테이블을 올바른 FK 로 재생성해 복구한다.
    """
    cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql LIKE '%_old\"(%' ESCAPE '\\'"
    )
    # LIKE 패턴이 방언을 타므로 파이썬 쪽에서 판정한다
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    broken = []
    for name, sql in cursor.fetchall():
        if not sql:
            continue
        for ref in re.findall(r'REFERENCES\s+"?(\w+)"?', sql):
            if ref.endswith("_old"):
                broken.append((name, sql, ref))
                break

    for name, sql, ref in broken:
        target = ref[: -len("_old")]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (ref,))
        if cursor.fetchone():
            continue  # 해당 _old 테이블이 실제로 살아 있으면 건드리지 않는다

        fixed_sql = re.sub(rf'REFERENCES\s+"?{re.escape(ref)}"?', f"REFERENCES {target}", sql)
        tmp = f"{name}__fkfix"
        fixed_sql = re.sub(rf'CREATE TABLE\s+"?{re.escape(name)}"?', f"CREATE TABLE {tmp}", fixed_sql, count=1)

        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute(fixed_sql)

        cursor.execute(f"PRAGMA table_info({name})")
        cols = ", ".join(f'"{r[1]}"' for r in cursor.fetchall())
        # 부모에 없는 행(고아)은 옮기지 않는다
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (target,))
        if cursor.fetchone():
            fk_col = None
            for col_sql in re.findall(r'FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+"?(\w+)"?', sql):
                if col_sql[1] == ref:
                    fk_col = col_sql[0]
                    break
            if fk_col:
                cursor.execute(
                    f"INSERT INTO {tmp} ({cols}) SELECT {cols} FROM {name} "
                    f"WHERE {fk_col} IN (SELECT id FROM {target})"
                )
            else:
                cursor.execute(f"INSERT INTO {tmp} ({cols}) SELECT {cols} FROM {name}")
        else:
            cursor.execute(f"INSERT INTO {tmp} ({cols}) SELECT {cols} FROM {name}")

        cursor.execute(f"DROP TABLE {name}")
        cursor.execute(f"ALTER TABLE {tmp} RENAME TO {name}")
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON")
        print(f"[migrate] {name} 의 깨진 FK 복구: {ref} -> {target}")


def _clean_orphan_rows(cursor, conn):
    """FK 가 꺼져 있던 동안 쌓인 고아 행 정리."""
    cleanups = [
        ("party_rooms", "UPDATE party_rooms SET character_id = NULL "
                        "WHERE character_id IS NOT NULL "
                        "AND character_id NOT IN (SELECT id FROM characters)"),
        ("party_rooms", "UPDATE party_rooms SET story_id = NULL "
                        "WHERE story_id IS NOT NULL "
                        "AND story_id NOT IN (SELECT id FROM stories)"),
        ("party_members", "DELETE FROM party_members "
                          "WHERE room_id NOT IN (SELECT id FROM party_rooms)"),
        ("party_messages", "DELETE FROM party_messages "
                           "WHERE room_id NOT IN (SELECT id FROM party_rooms)"),
        ("character_tags", "DELETE FROM character_tags "
                           "WHERE character_id NOT IN (SELECT id FROM characters)"),
        ("character_images", "DELETE FROM character_images "
                             "WHERE character_id NOT IN (SELECT id FROM characters)"),
        ("character_backgrounds", "DELETE FROM character_backgrounds "
                                  "WHERE character_id NOT IN (SELECT id FROM characters)"),
        ("character_likes", "DELETE FROM character_likes "
                            "WHERE character_id NOT IN (SELECT id FROM characters)"),
        ("character_bookmarks", "DELETE FROM character_bookmarks "
                                "WHERE character_id NOT IN (SELECT id FROM characters)"),
        ("post_character_tags", "DELETE FROM post_character_tags "
                                "WHERE character_id NOT IN (SELECT id FROM characters)"),
    ]
    total = 0
    for table, sql in cleanups:
        try:
            cursor.execute(sql)
            if cursor.rowcount > 0:
                total += cursor.rowcount
                print(f"[migrate] {table} 고아 행 정리: {cursor.rowcount}건")
        except sqlite3.OperationalError:
            pass
    if total:
        conn.commit()


def _migrate_party_rooms_nullable(cursor, conn):
    cursor.execute("PRAGMA table_info(party_rooms)")
    cols = {row[1]: row for row in cursor.fetchall()}
    story_id_notnull = (
        cols.get("story_id", (None,) * 4)[3] if "story_id" in cols else None
    )
    if "character_id" in cols and story_id_notnull == 0:
        return

    cursor.execute("ALTER TABLE party_rooms RENAME TO party_rooms_old")
    cursor.execute("""
        CREATE TABLE party_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            story_id INTEGER,
            character_id TEXT,
            host_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            max_members INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id),
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (host_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        INSERT INTO party_rooms (id, code, story_id, host_id, status, max_members, created_at)
        SELECT id, code, story_id, host_id, status, max_members, created_at FROM party_rooms_old
    """)
    cursor.execute("DROP TABLE party_rooms_old")
    conn.commit()


def _migrate_party_rooms_status_check(cursor, conn):
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='party_rooms'"
    )
    table_sql = cursor.fetchone()[0]
    if "CHECK(status IN" in table_sql:
        return

    cursor.execute("ALTER TABLE party_rooms RENAME TO party_rooms_old")
    cursor.execute("""
        CREATE TABLE party_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            story_id INTEGER,
            character_id TEXT,
            host_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting' CHECK(status IN ('waiting', 'active', 'closed')),
            max_members INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id),
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (host_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        INSERT INTO party_rooms (id, code, story_id, character_id, host_id, status, max_members, created_at)
        SELECT id, code, story_id, character_id, host_id, status, max_members, created_at FROM party_rooms_old
    """)
    cursor.execute("DROP TABLE party_rooms_old")
    conn.commit()


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 유저
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_adult INTEGER DEFAULT 0,
            safety_mode INTEGER DEFAULT 1,
            token_purchased INTEGER DEFAULT 0,
            token_event INTEGER DEFAULT 0,
            token_balance INTEGER DEFAULT 100,
            output_length TEXT DEFAULT 'medium',
            image_mode_chat INTEGER DEFAULT 1,
            image_mode_bg INTEGER DEFAULT 1,
            image_mode_bottom INTEGER DEFAULT 1,
            image_mode_multi INTEGER DEFAULT 0,
            consecutive_purchase_days INTEGER DEFAULT 0,
            last_purchase_date TEXT DEFAULT NULL,
            last_attendance_date TEXT DEFAULT NULL,
            attendance_streak INTEGER DEFAULT 0,
            ad_watched_today INTEGER DEFAULT 0,
            last_ad_date TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 업적 정의 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            reward_token INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 유저 업적 달성 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_code TEXT NOT NULL,
            achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, achievement_code),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 캐릭터
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            prompt TEXT NOT NULL,
            first_message TEXT DEFAULT '',
            situation TEXT DEFAULT '',
            visibility TEXT DEFAULT 'public',
            is_adult INTEGER DEFAULT 0,
            image_url TEXT DEFAULT '',
            chat_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 캐릭터 태그
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    # 대화 기록
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            user_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 메시지 평가 (좋아요/싫어요)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            rating TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 유저노트
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 페르소나
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            name TEXT DEFAULT '',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 메모리북
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 좋아요
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 팔로우
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(follower_id, following_id),
            FOREIGN KEY (follower_id) REFERENCES users(id),
            FOREIGN KEY (following_id) REFERENCES users(id)
        )
    """)

    # 배너
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image_url TEXT NOT NULL,
            link_url TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            order_num INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 건의사항
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT DEFAULT '기타',
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 고객센터
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            answer TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 토큰 내역
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            token_type TEXT NOT NULL,
            reason TEXT NOT NULL,
            expires_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 구매 내역
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            token_amount INTEGER NOT NULL,
            payment_method TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 스토리
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            genre TEXT DEFAULT '기타',
            background TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            image_url TEXT DEFAULT '',
            recommended_players INTEGER DEFAULT 4,
            min_players INTEGER DEFAULT 2,
            max_players INTEGER DEFAULT 6,
            is_official INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 파티 방
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS party_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            story_id INTEGER,
            character_id TEXT,
            host_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            max_members INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id),
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (host_id) REFERENCES users(id)
        )
    """)
    _migrate_party_rooms_nullable(cursor, conn)
    _migrate_party_rooms_status_check(cursor, conn)

    # 파티 멤버
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS party_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            character_stats TEXT NOT NULL,
            is_ready INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES party_rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 파티 메시지
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS party_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES party_rooms(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(blocker_id, blocked_id),
            FOREIGN KEY (blocker_id) REFERENCES users(id),
            FOREIGN KEY (blocked_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT DEFAULT '',
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS party_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code TEXT NOT NULL,
            inviter_id INTEGER NOT NULL,
            invitee_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(room_code, invitee_id),
            FOREIGN KEY (inviter_id) REFERENCES users(id),
            FOREIGN KEY (invitee_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_image_url TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE achievements ADD COLUMN prefix_title TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE achievements ADD COLUMN suffix_title TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN equipped_prefix TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN equipped_suffix TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN memory_pass_expires_at TIMESTAMP DEFAULT NULL")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN memory_chunk_limit INTEGER DEFAULT 20")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN output_multiplier REAL DEFAULT 1.0")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE characters ADD COLUMN category TEXT DEFAULT '기타'")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN suspended INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN streak_reward_claimed_at TIMESTAMP DEFAULT NULL")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN consecutive_purchase_start_date TEXT DEFAULT NULL")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN purchase_streak_total_tokens INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE characters ADD COLUMN view_count INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE characters ADD COLUMN party_enabled INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE characters ADD COLUMN likes TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("ALTER TABLE characters ADD COLUMN dislikes TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_type ON community_posts(post_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_genre ON community_posts(genre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_user ON community_posts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_post ON post_character_tags(post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_char ON post_character_tags(character_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post ON community_comments(post_id)")
        conn.commit()
    except:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            emotion TEXT NOT NULL DEFAULT 'neutral',
            image_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    # 캐릭터 상황별 배경
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_backgrounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            situation TEXT NOT NULL DEFAULT 'default',
            image_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    # 친구 초대
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE,
            referrer_ip TEXT NOT NULL,
            referred_ip TEXT NOT NULL,
            reward_given INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users(id),
            FOREIGN KEY (referred_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_registrations (
            ip TEXT PRIMARY KEY,
            count INTEGER DEFAULT 1,
            last_registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 초대 코드
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            content TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            is_pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 커뮤니티 게시글
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            post_type TEXT DEFAULT 'general',
            genre TEXT,
            ai_description TEXT,
            image_url TEXT,
            is_adult INTEGER DEFAULT 0,
            is_blurred INTEGER DEFAULT 0,
            party_character_id TEXT,
            party_room_id TEXT,
            party_max INTEGER,
            party_current INTEGER DEFAULT 1,
            party_status TEXT DEFAULT 'open',
            status TEXT DEFAULT 'active',
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 게시글 캐릭터 태그
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_character_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id),
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    # 커뮤니티 댓글
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 커뮤니티 좋아요
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(post_id, user_id),
            FOREIGN KEY (post_id) REFERENCES community_posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── 캐릭터 구조화 필드 영속화 ────────────────────────────
    # age/job/personality/speech_style 이 컬럼 없이 prompt 텍스트에만 박혀 있었다.
    # 그래서 수정 API 로 해당 필드를 안 보내면 `request.age or 0` 이 먹혀
    # 25세 캐릭터가 저장 한 번에 "나이: 0세" 가 됐다 (아동 콘텐츠 방지 규칙과 정면 충돌).
    for col, ddl in (
        ("age", "ALTER TABLE characters ADD COLUMN age INTEGER DEFAULT 20"),
        ("job", "ALTER TABLE characters ADD COLUMN job TEXT DEFAULT ''"),
        ("personality", "ALTER TABLE characters ADD COLUMN personality TEXT DEFAULT ''"),
        ("speech_style", "ALTER TABLE characters ADD COLUMN speech_style TEXT DEFAULT ''"),
    ):
        try:
            cursor.execute(ddl)
            conn.commit()
        except sqlite3.OperationalError:
            pass
    _backfill_character_fields(cursor, conn)

    # ── 깨진 FK / 고아 행 복구 ────────────────────────────────
    _repair_dangling_fk_references(cursor, conn)
    _clean_orphan_rows(cursor, conn)

    # ── 결제/지급 멱등키 ──────────────────────────────────────
    # 같은 요청이 두 번 들어와도 지급이 두 번 일어나지 않게 하는 유일한 장치
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_grants (
            idempotency_key TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            token_type TEXT NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── 기억 품질 계측 ────────────────────────────────────────
    # "기억을 얼마나 잘하는가" 를 감으로 말고 숫자로 보기 위한 이벤트 로그.
    # 추출 성공/실패, 요약 발동, 주입된 기억 수를 남긴다.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT NOT NULL,
            session_id TEXT DEFAULT '',
            event_type TEXT NOT NULL,
            turn_count INTEGER DEFAULT 0,
            value INTEGER DEFAULT 0,
            detail TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # dislike 가 기억 문제인지 말투 문제인지 구분할 수 있게 사유 태그를 받는다
    try:
        cursor.execute("ALTER TABLE message_ratings ADD COLUMN reason TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # ── 인덱스 ────────────────────────────────────────────────
    # chat_history 는 인덱스가 하나도 없는 상태에서 매 채팅마다 COUNT(*) 풀스캔을
    # 두 번 돌고 있었다. 아래 인덱스가 그 비용을 없앤다.
    for stmt in (
        "CREATE INDEX IF NOT EXISTS idx_chat_user_char_sess ON chat_history(user_id, character_id, session_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_chat_user_role      ON chat_history(user_id, role)",
        "CREATE INDEX IF NOT EXISTS idx_chat_session        ON chat_history(session_id, character_id)",
        "CREATE INDEX IF NOT EXISTS idx_token_hist_user     ON token_history(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_token_hist_expire   ON token_history(token_type, expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_char_public         ON characters(visibility, is_adult, like_count)",
        "CREATE INDEX IF NOT EXISTS idx_char_owner          ON characters(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_char_tags_tag       ON character_tags(tag, character_id)",
        "CREATE INDEX IF NOT EXISTS idx_party_member_room   ON party_members(room_id, user_id)",
        "CREATE INDEX IF NOT EXISTS idx_party_msg_room      ON party_messages(room_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_notif_user          ON notifications(user_id, is_read, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_likes_char          ON character_likes(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_bookmarks_user      ON character_bookmarks(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_refresh_user        ON refresh_tokens(user_id, expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_memory_user_char    ON memory_book(user_id, character_id, id)",
        "CREATE INDEX IF NOT EXISTS idx_mem_events_type     ON memory_events(event_type, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_mem_events_user     ON memory_events(user_id, character_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_notes_user_char     ON user_notes(user_id, character_id)",
        "CREATE INDEX IF NOT EXISTS idx_persona_user_char   ON user_personas(user_id, character_id)",
    ):
        try:
            cursor.execute(stmt)
        except sqlite3.OperationalError:
            pass

    # ── 잔액 정합성 복구 ──────────────────────────────────────
    # token_balance 를 별도 컬럼으로 이중 관리해 온 탓에 실제로 drift 가 발생해 있었다.
    # 앞으로 잔액은 token_purchased + token_event 를 단일 진실로 삼고,
    # token_balance 는 그 파생값으로만 동기화한다.
    cursor.execute("""
        UPDATE users
           SET token_balance = token_purchased + token_event
         WHERE token_balance != token_purchased + token_event
    """)
    if cursor.rowcount:
        print(f"[migrate] token_balance 정합성 복구: {cursor.rowcount}건")

    conn.commit()
    conn.close()
