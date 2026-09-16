# Stellia Backend

FastAPI + SQLite(운영 전환 시 MySQL) + Gemini 2.5 Flash

## 실행

```bash
cp .env.example .env       # 값 채우기 (JWT_SECRET 은 32자 이상 필수)
pip install -r requirements.txt
uvicorn main:app --reload
```

`http://localhost:8000/docs` (production 에서는 비활성)

## 환경변수

| 키 | 필수 | 설명 |
|---|---|---|
| `JWT_SECRET` | ✅ | 32자 이상. `openssl rand -hex 32`. 없거나 짧으면 **기동 거부** |
| `GEMINI_API_KEY` | ✅ | 없으면 기동 거부 |
| `ENV` | | `development` / `production`. production 은 docs 비활성 + 성인인증 자기선언 차단 |
| `DB_PATH` | | 비우면 `backend/chatbot.db` (항상 절대경로로 변환) |
| `CORS_ORIGINS` | | 쉼표 구분 |
| `TRUSTED_PROXY` | | `none`(기본) / `cloudflare`. Cloudflare 뒤가 아니면 절대 바꾸지 말 것 — 헤더 위조로 레이트리밋이 우회된다 |
| `REDIS_URL` | | 비우면 인메모리. **워커 2개 이상이면 필수** |
| `RUN_SCHEDULER` | | 워커를 여러 개 띄울 땐 전용 프로세스 1개만 `1` |
| `RATE_LIMIT_ENABLED` | | 테스트에서만 `0` |

## 구조

```
core/            config · db(트랜잭션) · security(JWT) · deps(권한)
                 token_service(원장) · middleware(보안) · cache(Redis)
                 serializers(응답 필터) · logging_mw(요청추적)
chat/            router · llm(비동기 Gemini) · session_store
<domain>/router.py
scripts/         backup_db · check_integrity · make_admin
tests/
```

### 지켜야 할 규칙

- **DB 접근은 `core.db` 경유.** `with transaction() as cur:` / `with read_only() as cur:`
  직접 `sqlite3.connect` 를 쓰면 FK·WAL·타임아웃 설정이 빠지고 커넥션이 샌다.
- **토큰 지급/차감은 `core.token_service` 만.** `users.token_*` 을 직접 UPDATE 하면
  잔액이 어긋난다(실제로 어긋났던 이력 있음). 지급에는 `idempotency_key` 필수.
- **캐릭터 접근은 `deps.assert_character_access()`.** 라우터마다 따로 검사하면 빠뜨린다.
- **응답에 `SELECT c.*` 금지.** `core.serializers.public_character()` 로 prompt 를 거른다.
- **LLM 호출은 `chat.llm.generate()`(await).** 동기 호출은 이벤트 루프를 막는다.

## 운영

```bash
python scripts/make_admin.py you@example.com   # 최초 관리자 (API 로는 불가)
python scripts/check_integrity.py              # 정합성 점검 (배포 후 / 정기)
python scripts/backup_db.py --keep 14          # WAL 안전 온라인 백업
```

cron 예시

```
0 4 * * *  cd /app && python scripts/backup_db.py --keep 14
*/30 * * * * cd /app && python scripts/check_integrity.py || /usr/bin/notify.sh
```

## 배포

```bash
docker compose up -d --build     # app(워커2) + scheduler(1) 분리
```

`GET /health` 는 DB 프로브를 포함한다(DB 이상 시 503). 모든 응답에 `X-Request-ID`.

## 아직 안 된 것

- PG 연동 (사업자등록 후). 그 전까지 토큰/메모리패스 **지급은 관리자 전용**
- 광고 SSV — 현재는 일일 한도가 유일한 방어선
- 본인확인(PASS/NICE) — 그 전까지 production 에서 성인인증 비활성
- 비밀번호 재설정 — FAQ 에는 안내돼 있으나 API 없음 (메일 발송 수단 결정 필요)
- MySQL 전환, FCM, 이미지 생성
