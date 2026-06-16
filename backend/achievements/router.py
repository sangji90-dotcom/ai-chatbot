from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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
    {"code": "first_signup", "title": "새로운 시작", "description": "회원가입을 완료했습니다.", "difficulty": "bronze", "reward_token": 500, "prefix_title": "별의", "suffix_title": "방랑자"},
    {"code": "first_chat", "title": "첫 대화", "description": "처음으로 AI와 대화했습니다.", "difficulty": "bronze", "reward_token": 500, "prefix_title": "", "suffix_title": "수다쟁이"},
    {"code": "first_follow", "title": "첫 팔로우", "description": "처음으로 창작자를 팔로우했습니다.", "difficulty": "bronze", "reward_token": 500, "prefix_title": "별빛", "suffix_title": "탐험가"},
    {"code": "first_like", "title": "첫 좋아요", "description": "처음으로 캐릭터에 좋아요를 눌렀습니다.", "difficulty": "bronze", "reward_token": 500, "prefix_title": "", "suffix_title": "취향저격"},
    {"code": "attendance_1", "title": "출석 1일", "description": "첫 출석을 완료했습니다.", "difficulty": "bronze", "reward_token": 500, "prefix_title": "성실한", "suffix_title": ""},
    {"code": "first_character", "title": "첫 캐릭터", "description": "처음으로 캐릭터를 생성했습니다.", "difficulty": "bronze", "reward_token": 500, "prefix_title": "새내기", "suffix_title": "창작자"},
    # 실버 (1000)
    {"code": "chat_10", "title": "대화 10회", "description": "총 10회 대화했습니다.", "difficulty": "silver", "reward_token": 1000, "prefix_title": "", "suffix_title": "이야기꾼"},
    {"code": "chat_single_10", "title": "단골손님", "description": "한 캐릭터와 10회 대화했습니다.", "difficulty": "silver", "reward_token": 1000, "prefix_title": "", "suffix_title": "단골손님"},
    {"code": "attendance_7", "title": "출석 7일", "description": "7일 연속 출석했습니다.", "difficulty": "silver", "reward_token": 1000, "prefix_title": "꾸준한", "suffix_title": "별"},
    {"code": "first_follower", "title": "첫 팔로워", "description": "첫 번째 팔로워가 생겼습니다.", "difficulty": "silver", "reward_token": 1000, "prefix_title": "", "suffix_title": "인싸"},
    {"code": "anniversary_30", "title": "가입 30일", "description": "가입한지 30일이 됐습니다.", "difficulty": "silver", "reward_token": 1000, "prefix_title": "한달의", "suffix_title": ""},
    # 골드 (1500)
    {"code": "chat_50", "title": "대화 50회", "description": "총 50회 대화했습니다.", "difficulty": "gold", "reward_token": 1500, "prefix_title": "수다", "suffix_title": "달인"},
    {"code": "chat_single_50", "title": "찐팬", "description": "한 캐릭터와 50회 대화했습니다.", "difficulty": "gold", "reward_token": 1500, "prefix_title": "", "suffix_title": "찐팬"},
    {"code": "attendance_30", "title": "출석 30일", "description": "30일 연속 출석했습니다.", "difficulty": "gold", "reward_token": 1500, "prefix_title": "30일의", "suffix_title": "성실함"},
    {"code": "follower_10", "title": "팔로워 10명", "description": "팔로워가 10명이 됐습니다.", "difficulty": "gold", "reward_token": 1500, "prefix_title": "떠오르는", "suffix_title": "창작자"},
    {"code": "character_5", "title": "캐릭터 5개", "description": "캐릭터를 5개 생성했습니다.", "difficulty": "gold", "reward_token": 1500, "prefix_title": "다작", "suffix_title": "창작자"},
    {"code": "anniversary_100", "title": "가입 100일", "description": "가입한지 100일이 됐습니다.", "difficulty": "gold", "reward_token": 1500, "prefix_title": "백일의", "suffix_title": ""},
    # 플래티넘 (2000)
    {"code": "chat_100", "title": "대화 100회", "description": "총 100회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "대화의", "suffix_title": "신"},
    {"code": "chat_500", "title": "대화 500회", "description": "총 500회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "전설의", "suffix_title": "수다왕"},
    {"code": "chat_1000", "title": "대화 1000회", "description": "총 1000회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "불멸의", "suffix_title": "대화왕"},
    {"code": "chat_single_100", "title": "소울메이트", "description": "한 캐릭터와 100회 대화했습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "", "suffix_title": "소울메이트"},
    {"code": "attendance_100", "title": "출석 100일", "description": "100일 연속 출석했습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "백일의", "suffix_title": "별빛"},
    {"code": "follower_50", "title": "팔로워 50명", "description": "팔로워가 50명이 됐습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "주목받는", "suffix_title": "창작자"},
    {"code": "follower_100", "title": "팔로워 100명", "description": "팔로워가 100명이 됐습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "스텔리아의", "suffix_title": "스타"},
    {"code": "character_10", "title": "캐릭터 10개", "description": "캐릭터를 10개 생성했습니다.", "difficulty": "platinum", "reward_token": 2000, "prefix_title": "세계를 만드는", "suffix_title": ""},
    # 기념일 (3650)
    {"code": "anniversary_365", "title": "1주년 🎉", "description": "가입한지 1년이 됐습니다!", "difficulty": "anniversary", "reward_token": 3650, "prefix_title": "1주년을 함께한", "suffix_title": ""},
    {"code": "anniversary_730", "title": "2주년 🎉", "description": "가입한지 2년이 됐습니다!", "difficulty": "anniversary", "reward_token": 3650, "prefix_title": "2주년을 함께한", "suffix_title": ""},
]

DIFFICULTY_COLOR = {
    "bronze": "#cd7f32",
    "silver": "#c0c0c0",
    "gold": "#f6c65b",
    "platinum": "#8b7cff",
    "anniversary": "#ff9af3",
}


def init_achievements():
    conn = get_db()
    cursor = conn.cursor()
    for a in ACHIEVEMENTS:
        cursor.execute("""
            INSERT OR IGNORE INTO achievements
            (code, title, description, difficulty, reward_token, prefix_title, suffix_title)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (a["code"], a["title"], a["description"], a["difficulty"],
              a["reward_token"], a.get("prefix_title", ""), a.get("suffix_title", "")))
        cursor.execute("""
            UPDATE achievements SET prefix_title = ?, suffix_title = ? WHERE code = ?
        """, (a.get("prefix_title", ""), a.get("suffix_title", ""), a["code"]))
    conn.commit()
    conn.close()


def check_and_grant(user_id: int, code: str):
    from tokens.router import add_token

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

    # 업적 달성 토큰 지급
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


class EquipTitleRequest(BaseModel):
    prefix_title: str = ""
    suffix_title: str = ""


@router.patch("/me/equip-title", summary="칭호 장착")
async def equip_title(
        request: EquipTitleRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    # 앞 칭호 검증
    if request.prefix_title:
        cursor.execute("""
            SELECT a.prefix_title FROM achievements a
            JOIN user_achievements ua ON a.code = ua.achievement_code
            WHERE ua.user_id = ? AND a.prefix_title = ?
        """, (current_user["id"], request.prefix_title))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=403, detail="달성하지 않은 칭호예요.")

    # 뒤 칭호 검증
    if request.suffix_title:
        cursor.execute("""
            SELECT a.suffix_title FROM achievements a
            JOIN user_achievements ua ON a.code = ua.achievement_code
            WHERE ua.user_id = ? AND a.suffix_title = ?
        """, (current_user["id"], request.suffix_title))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=403, detail="달성하지 않은 칭호예요.")

    cursor.execute("""
        UPDATE users SET equipped_prefix = ?, equipped_suffix = ? WHERE id = ?
    """, (request.prefix_title, request.suffix_title, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "칭호 장착 완료"}


@router.delete("/me/equip-title", summary="칭호 해제")
async def unequip_title(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET equipped_prefix = '', equipped_suffix = '' WHERE id = ?
    """, (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "칭호 해제 완료"}