"""업로드 확장자 판정 — polyglot 파일을 .html 로 저장하던 경로 차단."""
import pytest
from fastapi import HTTPException

from utils import EXT_BY_MIME, validate_image


def test_gif_polyglot_gets_gif_extension():
    payload = b"GIF89a" + b"<script>alert(1)</script>" + b"\x00" * 10
    mime = validate_image(payload)
    assert EXT_BY_MIME[mime] == "gif", "확장자는 filename 이 아니라 magic bytes 로 결정돼야 한다"


def test_html_rejected():
    with pytest.raises(HTTPException):
        validate_image(b"<html><script>alert(1)</script></html>")


def test_empty_rejected():
    with pytest.raises(HTTPException):
        validate_image(b"")
