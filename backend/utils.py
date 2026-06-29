from fastapi import HTTPException, UploadFile

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_SIZE = 10 * 1024 * 1024  # 10MB

# 매직바이트 시그니처
MAGIC_BYTES = {
    b'\xff\xd8\xff': "image/jpeg",
    b'\x89PNG': "image/png",
    b'GIF8': "image/gif",
    b'RIFF': "image/webp",
}

def validate_image(contents: bytes, max_size: int = MAX_SIZE):
    # 크기 검증
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기는 {max_size // (1024*1024)}MB 이하여야 합니다."
        )
    # 매직바이트 검증
    detected = None
    for magic, mime in MAGIC_BYTES.items():
        if contents[:len(magic)].startswith(magic):
            detected = mime
            break
    if not detected:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")
    return detected

async def read_and_validate_image(file: UploadFile, max_size: int = MAX_SIZE) -> bytes:
    # content_type 1차 검증
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="JPG, PNG, GIF, WEBP만 업로드 가능합니다.")
    contents = await file.read()
    # 매직바이트 2차 검증
    validate_image(contents, max_size)
    return contents