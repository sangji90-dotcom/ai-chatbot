"""2차 감사(잔여 라우터)에서 나온 구멍들의 회귀 테스트."""
import sqlite3

from core.config import DB_PATH
from tests.conftest import auth


def _uid(client, tok):
    return client.get("/users/me", headers=auth(tok)).json()["id"]


def _make_character(client, tok, visibility="public", name="테스터"):
    r = client.post("/characters", headers=auth(tok), json={
        "name": name, "age": 25, "job": "개발자", "personality": "차분함",
        "likes": "커피", "dislikes": "소음", "speech_style": "담백",
        "visibility": visibility,
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ── 배너: summary 엔 "(관리자)" 였지만 검사가 없었다 ────────────────────
def test_banner_create_requires_admin(client, user_a):
    r = client.post("/banners", headers=auth(user_a),
                    json={"title": "광고", "image_url": "/x.png", "link_url": "https://evil.example"})
    assert r.status_code == 403, "일반 유저가 메인 배너를 등록할 수 있으면 안 된다"


def test_banner_delete_requires_admin(client, user_a):
    assert client.delete("/banners/1", headers=auth(user_a)).status_code == 403
    assert client.patch("/banners/1/toggle", headers=auth(user_a)).status_code == 403


def test_banner_rejects_javascript_scheme(client, user_admin):
    r = client.post("/banners", headers=auth(user_admin), json={
        "title": "x", "image_url": "/ok.png", "link_url": "javascript:alert(1)",
    })
    assert r.status_code == 422


# ── 캐릭터 prompt 유출 ──────────────────────────────────────────────────
def test_like_list_hides_prompt_of_others(client, user_a, user_b):
    cid = _make_character(client, user_a, name="공개캐릭")
    assert client.post(f"/likes/{cid}", headers=auth(user_b)).status_code == 200

    rows = client.get("/likes/me", headers=auth(user_b)).json()
    target = next(r for r in rows if r["id"] == cid)
    assert "prompt" not in target, "남의 캐릭터 prompt 가 응답에 포함되면 안 된다"


def test_bookmark_list_hides_prompt(client, user_a, user_b):
    cid = _make_character(client, user_a, name="북마크대상")
    assert client.post(f"/likes/bookmarks/{cid}", headers=auth(user_b)).status_code == 200
    rows = client.get("/likes/bookmarks", headers=auth(user_b)).json()
    assert all("prompt" not in r for r in rows)


# ── 비공개 캐릭터 상호작용 차단 ─────────────────────────────────────────
def test_cannot_like_private_character(client, user_a, user_b):
    cid = _make_character(client, user_a, visibility="private", name="비공개1")
    assert client.post(f"/likes/{cid}", headers=auth(user_b)).status_code == 403


def test_cannot_bookmark_private_character(client, user_a, user_b):
    cid = _make_character(client, user_a, visibility="private", name="비공개2")
    assert client.post(f"/likes/bookmarks/{cid}", headers=auth(user_b)).status_code == 403


def test_follow_feed_excludes_private_characters(client, user_a, user_b):
    a_id = _uid(client, user_a)
    _make_character(client, user_a, visibility="private", name="숨김캐릭")
    client.post(f"/follows/{a_id}", headers=auth(user_b))

    feed = client.get("/follows/me/new-characters", headers=auth(user_b)).json()
    assert all(c["name"] != "숨김캐릭" for c in feed), "팔로우 피드에 private 캐릭터가 노출되면 안 된다"
    assert all("prompt" not in c for c in feed)


# ── 무인증 LLM 호출 ─────────────────────────────────────────────────────
def test_support_ask_requires_auth(client):
    r = client.post("/support/ask", json={"message": "토큰 어떻게 충전해요?"})
    assert r.status_code == 401, "무인증으로 Gemini 를 호출할 수 있으면 비용 공격이 가능하다"


def test_support_inquiry_requires_auth(client):
    r = client.post("/support/inquiries", json={"title": "t", "content": "c"})
    assert r.status_code == 401


def test_suggestion_requires_auth(client):
    r = client.post("/suggestions", json={"category": "기타", "content": "건의합니다"})
    assert r.status_code == 401


# ── 리뷰: 대화 이력 없는 평점 조작 ──────────────────────────────────────
def test_review_requires_chat_history(client, user_a, user_b):
    cid = _make_character(client, user_a, name="리뷰대상")
    r = client.post(f"/reviews/{cid}", headers=auth(user_b), json={"rating": 1, "content": "별로"})
    assert r.status_code == 403, "대화한 적 없는 계정의 평점 조작을 막아야 한다"


# ── 커뮤니티 댓글 수정/삭제 (기존에 API 자체가 없었음) ──────────────────
def test_comment_edit_and_delete(client, user_a, user_b):
    post = client.post("/community", headers=auth(user_a),
                       data={"content": "안녕하세요", "post_type": "general"})
    assert post.status_code == 200, post.text
    pid = post.json()["id"]

    assert client.post(f"/community/{pid}/comments", headers=auth(user_b),
                       json={"content": "첫 댓글"}).status_code == 200

    detail = client.get(f"/community/{pid}").json()
    comment_id = detail["comments"][0]["id"]

    # 남의 댓글은 수정 불가
    assert client.put(f"/community/comments/{comment_id}", headers=auth(user_a),
                      json={"content": "위조"}).status_code == 404
    # 본인 댓글은 수정 가능
    assert client.put(f"/community/comments/{comment_id}", headers=auth(user_b),
                      json={"content": "수정됨"}).status_code == 200
    # 게시글 작성자는 삭제 불가(관리자/본인만)
    assert client.delete(f"/community/comments/{comment_id}",
                         headers=auth(user_a)).status_code == 403
    assert client.delete(f"/community/comments/{comment_id}",
                         headers=auth(user_b)).status_code == 200


def test_cannot_tag_private_character_in_post(client, user_a, user_b):
    cid = _make_character(client, user_a, visibility="private", name="비밀태그")
    post = client.post("/community", headers=auth(user_b),
                       data={"content": "태그 시도", "character_ids": cid})
    assert post.status_code == 200
    detail = client.get(f"/community/{post.json()['id']}").json()
    assert detail["character_tags"] == [], "남의 private 캐릭터가 태그로 노출되면 안 된다"


# ── 캐릭터 수정 시 나이·직업이 날아가던 버그 ────────────────────────────
def test_edit_preserves_age_and_job(client, user_a):
    """age/job 이 컬럼 없이 prompt 텍스트에만 있었다.

    수정 API 에서 해당 필드를 안 보내면 `request.age or 0` 이 적용돼
    25세 캐릭터가 저장 한 번에 '나이: 0세' 가 됐다.
    """
    import sqlite3
    from core.config import DB_PATH

    created = client.post("/characters", headers=auth(user_a), json={
        "name": "나이보존", "age": 27, "job": "수의사", "personality": "침착함",
        "likes": "산책", "dislikes": "소음", "speech_style": "차분함",
    })
    assert created.status_code == 200, created.text
    cid = created.json()["id"]

    # FE 수정 화면은 age/job 을 보내지 않는다 — 그 상황을 그대로 재현
    r = client.put(f"/characters/{cid}", headers=auth(user_a),
                   json={"description": "설명만 수정"})
    assert r.status_code == 200, r.text

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT age, job, personality, prompt FROM characters WHERE id = ?", (cid,)
    ).fetchone()
    conn.close()

    assert row["age"] == 27, "수정 후 나이가 바뀌면 안 된다"
    assert row["job"] == "수의사"
    assert row["personality"] == "침착함"
    assert "나이: 27세" in row["prompt"], "프롬프트와 컬럼이 어긋나면 안 된다"
    assert "나이: 0세" not in row["prompt"]


def test_edit_rejects_lowering_age_below_limit(client, user_a):
    created = client.post("/characters", headers=auth(user_a), json={
        "name": "나이낮추기", "age": 30, "job": "교사", "personality": "밝음",
        "likes": "책", "dislikes": "거짓말", "speech_style": "친절함",
    })
    cid = created.json()["id"]
    r = client.put(f"/characters/{cid}", headers=auth(user_a), json={"age": 15})
    assert r.status_code in (400, 422), "수정으로 미성년 캐릭터를 만들 수 있으면 안 된다"
