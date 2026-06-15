from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from deps import get_current_user, get_optional_user
from google import genai
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/support", tags=["고객센터"])
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ===== FAQ 데이터 =====
FAQ_LIST = [
    {"id": 1, "category": "토큰", "question": "토큰은 어떻게 충전하나요?", "answer": "앱 내 상점에서 토큰을 구매할 수 있습니다."},
    {"id": 2, "category": "토큰", "question": "무료 토큰을 받을 수 있나요?", "answer": "출석 체크, 광고 시청, 이벤트 참여를 통해 무료 토큰을 받을 수 있습니다."},
    {"id": 3, "category": "캐릭터", "question": "캐릭터는 어떻게 만드나요?", "answer": "캐릭터 생성 메뉴에서 이름, 설명, 프롬프트를 입력하면 나만의 캐릭터를 만들 수 있습니다."},
    {"id": 4, "category": "계정", "question": "비밀번호를 잊어버렸어요.", "answer": "로그인 화면의 '비밀번호 찾기'를 통해 이메일로 재설정할 수 있습니다."},
    {"id": 5, "category": "계정", "question": "회원 탈퇴는 어떻게 하나요?", "answer": "설정 > 계정 관리 > 회원 탈퇴에서 진행할 수 있습니다. 탈퇴 시 모든 데이터가 삭제됩니다."},
    {"id": 6, "category": "대화", "question": "대화 기록이 사라졌어요.", "answer": "대화 기록은 로그인 상태에서만 저장됩니다. 비로그인 상태에서는 앱 종료 시 삭제됩니다."},
    {"id": 7, "category": "결제", "question": "결제했는데 토큰이 안 들어왔어요.", "answer": "결제 후 최대 5분이 소요될 수 있습니다. 이후에도 문제가 있으면 문의해주세요."},
    {"id": 8, "category": "신고", "question": "불쾌한 콘텐츠를 신고하고 싶어요.", "answer": "해당 캐릭터 또는 메시지의 신고 버튼을 눌러 신고할 수 있습니다."},
]

FAQ_CONTEXT = "\n".join([
    f"Q: {f['question']}\nA: {f['answer']}" for f in FAQ_LIST
])

SUPPORT_SYSTEM_PROMPT = f"""당신은 AI 캐릭터 챗봇 서비스의 친절한 고객센터 AI입니다.
아래 FAQ를 참고하여 사용자 문의에 답변하세요.

[FAQ]
{FAQ_CONTEXT}

답변 규칙:
- FAQ에 있는 내용이면 해당 답변을 바탕으로 친절하게 답변하세요.
- FAQ에 없는 내용이면 "담당자에게 문의가 접수됩니다. 빠른 시일 내에 답변드리겠습니다."라고 안내하세요.
- 답변은 간결하고 친절하게 2~4문장으로 작성하세요.
- 모르는 내용을 추측하여 답변하지 마세요.
"""

# ===== Request Models =====
class InquiryRequest(BaseModel):
    title: str
    content: str

class AiAskRequest(BaseModel):
    message: str

# ===== FAQ 목록 =====
@router.get("/faq", summary="FAQ 목록")
async def get_faq(category: Optional[str] = None):
    if category:
        return [f for f in FAQ_LIST if f["category"] == category]
    return FAQ_LIST

# ===== AI 1차 답변 (문의 전 자동 답변) =====
@router.post("/ask", summary="AI 자동 답변")
async def ask_ai(request: AiAskRequest):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": request.message}]}],
        config={
            "system_instruction": SUPPORT_SYSTEM_PROMPT,
            "max_output_tokens": 500,
        }
    )
    answer = response.text
    needs_human = any(keyword in answer for keyword in ["담당자", "접수", "문의가 접수"])

    return {
        "answer": answer,
        "needs_human": needs_human  # True면 프론트에서 "문의 접수하기" 버튼 노출
    }

# ===== 문의 접수 =====
@router.post("/inquiries", summary="문의 접수")
async def create_inquiry(
        request: InquiryRequest,
        current_user: dict = Depends(get_optional_user)):

    # AI 1차 자동 답변 시도
    ai_answer = ""
    try:
        ai_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": f"{request.title}\n{request.content}"}]}],
            config={
                "system_instruction": SUPPORT_SYSTEM_PROMPT,
                "max_output_tokens": 500,
            }
        )
        ai_answer = ai_response.text
    except Exception:
        ai_answer = ""

    needs_human = not ai_answer or any(
        keyword in ai_answer for keyword in ["담당자", "접수", "문의가 접수"]
    )

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inquiries (user_id, title, content, answer, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        current_user["id"] if current_user else None,
        request.title,
        request.content,
        ai_answer if not needs_human else "",
        "answered" if not needs_human else "pending"
    ))
    conn.commit()
    inquiry_id = cursor.lastrowid
    conn.close()

    return {
        "inquiry_id": inquiry_id,
        "ai_answer": ai_answer if not needs_human else None,
        "status": "answered" if not needs_human else "pending",
        "message": "AI가 답변했습니다." if not needs_human else "담당자 검토 후 답변드리겠습니다."
    }

# ===== 내 문의 목록 =====
@router.get("/inquiries/me", summary="내 문의 목록")
async def get_my_inquiries(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, content, answer, status, created_at
        FROM inquiries WHERE user_id = ?
        ORDER BY created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ===== 내 문의 상세 =====
@router.get("/inquiries/{inquiry_id}", summary="문의 상세")
async def get_inquiry(
        inquiry_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, content, answer, status, created_at
        FROM inquiries WHERE id = ? AND user_id = ?
    """, (inquiry_id, current_user["id"]))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")
    return dict(row)