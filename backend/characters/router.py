@router.post("", summary="캐릭터 생성", description="새 캐릭터를 생성합니다.")
async def create_character(
        request: CreateCharacterRequest,
        current_user: dict = Depends(get_current_user)):
    from achievements.router import check_and_grant

    char_id = f"custom_{request.name}_{uuid.uuid4().hex[:8]}"

    prompt = f"""
너는 {request.name}라는 캐릭터야.

기본 정보:
- 이름: {request.name}
- 나이: {request.age}세
- 직업: {request.job}

성격 및 외모:
{request.personality}

좋아하는 것: {request.likes}
싫어하는 것: {request.dislikes}

말투:
{request.speech_style}

{"시작 상황: " + request.situation if request.situation else ""}

절대 규칙:
- AI라고 절대 말하지 않음
- 캐릭터를 절대 벗어나지 않음
"""

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO characters
        (id, user_id, name, description, prompt, first_message, situation, visibility, is_adult, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_id, current_user["id"], request.name, request.description,
        prompt, request.first_message, request.situation,
        request.visibility, request.is_adult, request.image_url
    ))

    for tag in request.tags:
        cursor.execute("INSERT INTO character_tags (character_id, tag) VALUES (?, ?)",
                       (char_id, tag))

    conn.commit()

    # 업적 체크
    cursor.execute("SELECT COUNT(*) as cnt FROM characters WHERE user_id = ?",
                   (current_user["id"],))
    count = cursor.fetchone()["cnt"]
    conn.close()

    if count == 1: check_and_grant(current_user["id"], "first_character")
    if count == 5: check_and_grant(current_user["id"], "character_5")
    if count == 10: check_and_grant(current_user["id"], "character_10")

    return {"id": char_id, "name": request.name, "message": "캐릭터 생성 완료"}