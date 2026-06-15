from fastapi import APIRouter, Depends
from database import get_db
from deps import get_current_user
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/achievements",
    tags=["업적"],
    responses={404: {"description": "찾을 수 없습니다"}}
)

ACHIEVEMENTS = [
    # 브론즈 (500)
    {"code": "first_signup", "title": "새로운 시작", "description": "회원가입을 완료했습니다.", "difficulty": "bronze", "reward_token": 500},
    {"code": "first_chat", "title": "첫 대화", "description": "처음으로 AI와 대화했습니다.", "difficulty": "bronze", "reward_token": 500},
    {"code": "first_follow", "title": "첫 팔로우", "description": "처음으로 창작자를 팔로우했습니다.", "difficulty": "bronze", "reward_token": 500},
    {"code": "first_like", "title": "첫 좋아요", "description": "처음으로 캐릭터에 좋아요를 눌렀습니다.", "difficulty": "bronze", "reward_token": 500},
    {"code": "attendance_1", "title": "출석 1일", "description": "첫 출석을 완료했습니다.", "difficulty": "bronze", "reward_token": 500},
    {"code": "first_character", "title": "첫 캐릭터", "description": "처음으로 캐릭터를 생성했습니다.", "difficulty": "bronze", "reward_token": 500},
    # 실버 (1000)
    {"code": "chat_10", "title": "대화 10회", "description": "총 10회 대화했습니다.", "difficulty": "silver", "reward_token": 1000},
    {"code": "chat_single_10", "title": "단골손님", "description": "한 캐릭터와 10회 대화했습니다.", "difficulty": "silver", "reward_token": 1000},
    {"code": "attendance_7", "title": "출석 7일", "description": "7일 연속 출석했습니다.", "difficulty": "silver", "reward_token": 1000},
    {"code": "first_follower", "title": "첫 팔로워", "description": "첫 번째 팔로워가 생겼습니다.", "difficulty": "silver", "reward_token": 1000},
    {"code": "anniversary_30", "title": "가입 30일", "description": "가입한지 30일이 됐습니다.", "difficulty": "silver", "reward_token": 1000},
    # 골드 (1500)
    {"code": "chat_50", "title": "대화 50회", "description": "총 50회 대화했습니다.", "difficulty": "gold", "reward_token": 1500},
    {"code": "chat_single_50", "title": "찐팬", "description": "한 캐릭터와 50회 대화했습니다.", "difficulty": "gold", "reward_token": 1500},
    {"code": "attendance_30", "title": "출석 30일", "description": "30일 연속 출석했습니다.", "difficulty": "gold", "reward_token": 1500},
    {"code": "follower_10", "title": "팔로워 10명", "description": "팔로워가 10명이 됐습니다.", "difficulty": "gold", "reward_token": 1500},
    {"code": "character_5", "title": "캐릭터 5개", "description": "캐릭터를 5개 생성했습니다.", "difficulty": "gold", "reward_token": 1500},
    {"code": "anniversary_100", "title": "가입 100일", "description": "가입한지 100일이 됐습니다.", "difficulty": "gold", "reward_token": 1500},
    # 플래티넘 (2000)
    {"code": "chat_100", "title": "대화 100회", "description": "총 100회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "chat_500", "title": "대화 500회", "description": "총 500회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "chat_1000", "title": "대화 1000회", "description": "총 1000회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "chat_single_100", "title": "소울메이트", "description": "한 캐릭터와 100회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "attendance_100", "title": "출석 100일", "description": "100일 연속 출석했습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "follower_50", "title": "팔로워 50명", "description": "팔로워가 50명이 됐습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "follower_100", "title": "팔로워 100명", "description": "팔로워가 100명이 됐습니다.", "difficulty": "platinum", "reward_token": 2000},
    {"code": "character_10", "title": "캐릭터 10개", "description": "캐릭터를 10개 생성했습니다.", "difficulty": "platinum", "reward_token": 2000},
    # 기념일 (3650)
    {"code": "anniversary_365", "title": "1주년 🎉", "description": "가입한지 1년이 됐습니다!", "difficulty": "anniversary", "reward_token": 3650},
    {"code": "anniversary_730", "title": "2주년 🎉", "description": "가입한지 2년이 됐습니다!", "difficulty": "anniversary", "reward_token": 3650},
]


def init_achievements():
    conn = get_db()
    cursor = conn.cursor()
    for a in ACHIEVEMENTS:
        cursor.execute("""
            INSERT OR IGNORE INTO achievements (code, title, description, difficulty, reward_token)
            VALUES (?, ?, ?, ?, ?)
        """, (a["code"], a["title"], a["description"], a["difficulty"], a["reward_token"]))
    conn.commit()
    conn.close()


def check_and_grant(user_id: int, code: str):
    from tokens.router import add_token  # 순환 import 방지

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM user_achievements WHERE user_id = ? AND achievement_code = ?
    """, (user_id, code))
    if cursor.fetchone():
        conn.close()
        return None

    cursor.execute("SELECT * FROM achievements WHERE code = ?", (code,))
    achievement = cursor.fetchone()
    if not achievement:
        conn.close()
        return None

    cursor.execute("""
        INSERT INTO user_achievements (user_id, achievement_code) VALUES (?, ?)
    """, (user_id, code))
    conn.commit()
    conn.close()

    expires_at = datetime.now() + timedelta(days=21)
    add_token(user_id, achievement["reward_token"], "event",
              f"업적 달성: {achievement['title']}", expires_at)

    return dict(achievement)


@router.get("", summary="전체 업적 목록")
async def get_achievements():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM achievements ORDER BY reward_token ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/me", summary="내 업적 현황")
async def get_my_achievements(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, ua.achieved_at FROM achievements a
        LEFT JOIN user_achievements ua
        ON a.code = ua.achievement_code AND ua.user_id = ?
        ORDER BY a.reward_token ASC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()

    return [
        {**dict(row), "achieved": row["achieved_at"] is not None}
        for row in rows
    ]