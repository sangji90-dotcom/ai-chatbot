"""업로드 검증.

확장자를 클라이언트가 보낸 filename 에서 뽑아 쓰면, magic bytes 를 통과하는
polyglot 파일(예: 'GIF89a<script>...')을 .html 로 저장할 수 있고, StaticFiles 가
이를 text/html 로 서빙하면 같은 오리진에서 스크립트가 실행된다
(= localStorage 의 access_token 탈취). 그래서 확장자는 **서버가 판정 결과로 결정**한다.
"""
from fastapi import HTTPException, UploadFile

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_SIZE = 10 * 1024 * 1024

MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}

EXT_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}


def _detect(contents: bytes) -> str | None:
    for magic, mime in MAGIC_BYTES.items():
        if contents.startswith(magic):
            return mime
    # WEBP: RIFF....WEBP
    if contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(contents: bytes, max_size: int = MAX_SIZE) -> str:
    if not contents:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기는 {max_size // (1024 * 1024)}MB 이하여야 합니다.",
        )
    detected = _detect(contents)
    if not detected:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")
    return detected


async def read_and_validate_image(file: UploadFile, max_size: int = MAX_SIZE) -> bytes:
    """하위 호환 — 내용만 반환."""
    contents, _ = await read_image_with_ext(file, max_size)
    return contents


async def read_image_with_ext(file: UploadFile, max_size: int = MAX_SIZE) -> tuple[bytes, str]:
    """(내용, 서버가 판정한 확장자) 를 반환한다. filename 은 신뢰하지 않는다."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="JPG, PNG, GIF, WEBP만 업로드 가능합니다.")

    contents = await file.read(max_size + 1)
    mime = validate_image(contents, max_size)
    return contents, EXT_BY_MIME[mime]
