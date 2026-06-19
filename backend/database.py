import sqlite3

DB_PATH = "chatbot.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
            story_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            max_members INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (story_id) REFERENCES stories(id),
            FOREIGN KEY (host_id) REFERENCES users(id)
        )
    """)

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
    
    conn.commit()
    conn.close()