from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from database import get_db
from deps import get_current_user, get_optional_user

router = APIRouter(
    prefix="/suggestions",
    tags=["건의사항"],
    responses={404: {"description": "찾을 수 없습니다"}}
)

CATEGORIES = ["기능", "버그", "캐릭터", "결제", "기타"]


class SuggestionRequest(BaseModel):
    category: str = "기타"
    content: str = Field(min_length=5, max_length=2000)

    @field_validator("category")
    @classmethod
    def _known(cls, v: str) -> str:
        return v if v in CATEGORIES else "기타"

@router.post("", summary="건의사항 제출", description="건의사항을 제출합니다.")
async def create_suggestion(
        request: SuggestionRequest,
        current_user: dict = Depends(get_current_user)):
    # 비로그인 허용 시 스팸을 막을 방법이 없어 인증 필수로 전환
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO suggestions (user_id, category, content)
        VALUES (?, ?, ?)
    """, (
        current_user["id"],
        request.category,
        request.content
    ))
    conn.commit()
    conn.close()
    return {"message": "건의사항 제출 완료"}

@router.get("/me", summary="내 건의사항 목록", description="내가 제출한 건의사항 목록을 반환합니다.")
async def get_my_suggestions(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM suggestions WHERE user_id = ? ORDER BY created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]