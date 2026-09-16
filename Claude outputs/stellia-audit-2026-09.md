# Stellia 전체 스캔 리포트 (2026-09-16)

- 대상: `ai-chatbot` (backend FastAPI 6,421 LOC / stellia-frontend 10,842 LOC / stellia_app 6,606 LOC)
- 마지막 커밋: `0d1bd95` (파티챗 Flutter) — 이후 uncommitted 변경 30+ 파일
- 결론: **기능 폭은 넓지만 런칭 가능한 상태가 아님.** 결제·토큰 경제가 서버 검증 없이 열려 있고, 동시성 설계가 없어 유저 2명부터 서비스가 멈춤.

---

## P0 — 지금 서버 열면 즉시 털리는 것

### 1. 결제 검증 없이 토큰 지급 (3개 엔드포인트)

| 엔드포인트 | 문제 |
|---|---|
| `POST /tokens/purchase/{package_id}` | PG 승인·영수증 검증 전무. 로그인만 하면 무한 금화 |
| `POST /purchases/manual` | `body.token_amount` 를 그대로 지급. 클라이언트가 액수를 결정 |
| `POST /tokens/memory-pass/purchase-cash` | 결제 없이 30일권 지급 |

- 실제 DB에 `purchases` 28건, user#2가 **343,240 금화** 보유 — 테스트 흔적이지만 운영에 그대로 나가면 즉시 악용.
- 조치: 세 엔드포인트 전부 `is_admin` 게이트 뒤로 옮기거나 라우터에서 제거. PG 연동 시 **webhook + 서버 측 금액 대조 + 멱등키(merchant_uid UNIQUE)** 가 유일한 지급 경로.

### 2. 토큰 잔액 정합성 이미 깨짐 (실측)

```
users.token_balance != token_purchased + token_event
  id=2  balance 354,840  vs  343,240 + 11,900 = 355,140   (-300)
  id=4  balance   6,000  vs      500 +  6,000 =   6,500   (-500)
```

- 원인 1: `purchases/manual` 이 `token_purchased` 만 증가시키고 `token_balance` 는 안 올림.
- 원인 2: `deduct_token()` 이 read → 판단 → write 를 트랜잭션 없이 수행. 동시 요청 시 이중 차감/무료 채팅.
- 원인 3: `token_balance` 를 별도 컬럼으로 이중 관리 → 구조적으로 drift가 불가피.
- 조치: **`token_balance` 컬럼 폐기.** 잔액은 `token_purchased + token_event` 파생값으로만 노출. 차감은 단일 UPDATE로 원자화:

```sql
UPDATE users
   SET token_event     = MAX(0, token_event - :amt),
       token_purchased = token_purchased - MAX(0, :amt - token_event)
 WHERE id = :uid
   AND token_purchased + token_event >= :amt;
-- rowcount == 0 이면 잔액 부족 → 402
```

### 3. `/chat` 에 인증·권한 검사 없음

- `Depends(get_optional_user)` → **비로그인도 대화 가능.** 토큰 차감도 안 되고 Gemini 호출은 나감. API 비용 무제한 노출.
- `visibility='private'` 캐릭터 검사 없음 → `character_id` 만 알면 남의 비공개 캐릭터로 대화 가능. (상세 조회 `GET /characters/{id}` 에는 검사가 있는데 `/chat` 에만 빠짐)
- `is_adult` 캐릭터 검사 없음 → 미인증 계정이 성인 캐릭터와 대화 가능.
- `DELETE /chat/{session_id}/{character_id}`, `POST /chat/new/{character_id}` — **인증 의존성 자체가 없음.**

### 4. 세션 캐시 크로스 유저 오염

```python
chat_histories = {}                                   # 전역 dict
session_key = f"{request.session_id}_{request.character_id}"   # user_id 없음
```

- DB 복원 쿼리에는 `user_id` 필터가 있지만 **메모리 캐시에는 없음.** A가 B의 `session_id` 를 알면 B의 대화 맥락을 그대로 이어받고, 그 내용이 A의 응답에 섞여 나옴. 개인정보 유출.
- 캐시가 영구 증가 → 메모리 누수. 멀티 워커에서는 워커마다 다른 히스토리.
- 조치: 키에 `user_id` 포함 + TTL LRU(또는 Redis)로 이전.

### 5. 자격증명·DB 파일이 GitHub에 올라가 있음

- `backend/.gitignore` 가 **UTF-16LE** 로 저장돼 git이 패턴을 인식 못 함 → `backend/chatbot.db`, 루트 `chatbot.db` 가 추적 중. **bcrypt 해시 포함 실제 유저 데이터가 원격에 존재.**
- `stellia-frontend/.env.production` 도 추적 중.
- 조치: `git rm --cached`, `.gitignore` 를 UTF-8(no BOM)로 재작성, **히스토리 정리(`git filter-repo`) + JWT_SECRET·GEMINI_API_KEY 즉시 회전.**

### 6. JWT 설계 결함

- `JWT_SECRET` fallback 이 `"your-secret-key-change-this"` — env 누락 시 조용히 공개 키로 동작.
- `get_current_user()` 가 `payload["type"]` 을 검사하지 않음 → **30일짜리 refresh token 으로 모든 API 호출 가능.** access token 2시간 만료가 무의미.
- `_issue_tokens()` 가 기존 refresh token 을 전부 DELETE → 멀티 디바이스 불가(웹 로그인하면 앱이 튕김).

### 7. 업로드 확장자 미검증 → 저장형 XSS

```python
ext = file.filename.split(".")[-1].lower()   # 화이트리스트 없음
open(f"{save_dir}/{uuid}.{ext}", "wb")
```

- magic bytes는 GIF/PNG 헤더만 보므로 `GIF89a<script>...` polyglot 을 `.html` 로 저장 가능 → `/images/...` 를 `StaticFiles` 가 `text/html` 로 서빙 → 같은 오리진에서 스크립트 실행 → **localStorage의 access_token 탈취.**
- 조치: ext를 magic bytes 판정 결과로 **서버가 결정**. 이미지는 별도 도메인/버킷(NCP Object Storage + Cloudflare) 서빙.

---

## P1 — 구조적 결함 (런칭 전 필수)

### 8. 동시성 설계 부재 — 가장 큰 병목

- 라우터 141개가 전부 `async def` 인데 내부는 **동기 `sqlite3` + 동기 `genai.generate_content()`**.
- Gemini 응답 3~10초 동안 **이벤트 루프 전체가 블로킹.** 동시 접속 2명이면 두 번째 유저는 앞 사람 응답이 끝날 때까지 대기. CBT에서 바로 드러날 문제.
- 조치 (택1, 권장은 둘 다):
  - DB 접근하는 라우터는 `def` 로 전환 → FastAPI가 threadpool에서 실행
  - LLM 호출은 `await client.aio.models.generate_content(...)` 비동기 API로 교체
- 추가: `/chat` 은 SSE 스트리밍으로 바꾸면 체감 지연이 사라짐.

### 9. SQLite → 운영 DB

- `DB_PATH = "chatbot.db"` **상대경로** → 실행 디렉터리에 따라 다른 DB가 열림 (루트에 0바이트 `chatbot.db` 가 이미 존재 = 실제로 밟은 적 있음).
- WAL 미설정, `PRAGMA foreign_keys` 미설정 → **FK 제약이 전혀 작동하지 않음.** 캐릭터 삭제 시 `chat_history`·`character_images`·`character_likes`·`character_bookmarks` 전부 고아 레코드.
- 쓰기 동시성 1 → 채팅 서비스에 부적합.
- 조치: MySQL 8 (NCP Cloud DB) + SQLAlchemy 2.0 + Alembic. 현재 `database.py` 의 `try: ALTER TABLE / except: pass` 26개 블록은 마이그레이션 도구로 대체.

### 10. 인덱스 전무

- 인덱스가 걸린 테이블은 `community_posts` / `post_character_tags` / `community_comments` 뿐.
- `chat_history` 는 **0개.** 그런데 매 채팅마다 업적 체크로 `COUNT(*)` 풀스캔을 2회 수행. 메시지 10만 건 시점에 채팅 응답이 초 단위로 느려짐.
- 최소 필요:

```sql
CREATE INDEX idx_chat_user_char_sess ON chat_history(user_id, character_id, session_id, created_at);
CREATE INDEX idx_chat_user_role      ON chat_history(user_id, role);
CREATE INDEX idx_token_hist_user     ON token_history(user_id, created_at);
CREATE INDEX idx_char_public         ON characters(visibility, is_adult, like_count);
CREATE INDEX idx_party_member_room   ON party_members(room_id, user_id);
```

- 업적 카운트는 `COUNT(*)` 대신 `users.total_chat_count` 카운터 컬럼으로 대체.

### 11. Rate Limit / XSS 미들웨어가 오히려 위험

- `rate_limit_store` = 프로세스 메모리 `defaultdict` → 워커 늘리면 무력화, 재시작하면 리셋, **키가 영구 누적돼 메모리 누수.**
- `get_client_ip()` 가 `X-Forwarded-For` 첫 값을 무조건 신뢰 → 헤더 위조로 rate limit 100% 우회. Cloudflare 앞단이면 `CF-Connecting-IP` 만 신뢰해야 함.
- XSS 정규식이 **모든 POST body 전체**에 걸림. `on\w+\s*=` 패턴 때문에 캐릭터 프롬프트나 롤플레이 대사에 `"...라고 말했다. reason= ..."` 같은 정상 텍스트가 들어가면 400. 반대로 JSON 유니코드 이스케이프(`<script`)는 그대로 통과.
- 조치: 입력 차단이 아니라 **출력 인코딩**으로. React는 기본 이스케이프되므로 실제 필요한 건 업로드/링크 sanitize. Rate limit 은 Cloudflare WAF 또는 Redis 기반으로.
- 커버리지도 비어 있음: `/characters/auto-complete` (Gemini 호출) 에 rate limit 없음 → 계정 하나로 API 비용 공격 가능.

### 12. 파티챗이 실제로 동작하지 않음

```python
elif msg_type == "chat":
    await websocket.send_json({...})   # 본인에게만 에코
```

- 브로드캐스트 없음(ConnectionManager 부재), `party_messages` 저장 없음, AI 진행 없음(`gemini_client` 를 import 만 하고 미사용).
- Flutter/React 화면은 완성돼 있는데 서버가 껍데기. **기능 목록에서 빼거나 재작성 둘 중 하나.**

### 13. 아동 성적 콘텐츠 필터가 사실상 무방비

```python
SEXUAL_KEYWORDS = ["로리", "쇼타", "loli", "shota", "어린이 성", "아동 성"]
```

- 유저 입력 6개 키워드 완전 일치 검사. 띄어쓰기·자모 분리·우회 표현에 전부 뚫림.
- **캐릭터 생성 시 나이 필드 검증이 없음** — `age: int` 에 하한이 없어 `age=12` 캐릭터를 `is_adult=1` 로 등록 가능. 프롬프트 안의 "절대 규칙" 문구는 강제력이 아님.
- 조치: `age >= 19` 서버 검증 + Gemini safety settings 명시 + 생성 캐릭터 사후 모더레이션 큐. 이건 법적 리스크라 CBT 전에 반드시.

### 14. 성인 인증이 자기 선언

- `POST /users/me/adult-verify` 가 조건 없이 `is_adult = 1`. 정보통신망법상 청소년유해매체물 제공 시 본인확인 의무 위반.
- 조치: PASS/NICE 본인확인 연동 전까지 **성인 캐릭터 기능 자체를 비활성화.**

### 15. 커넥션 누수 / 트랜잭션 경계 없음

- `update_character` / `delete_character` 의 404·403 분기에 `conn.close()` 누락.
- `purchases/router.py` 는 아예 `close()` 없음.
- `/chat` 은 Gemini 호출 수 초 동안 SQLite 커넥션을 연 채 유지 → write lock 점유.
- 출석/광고/구매 로직이 `conn 열기 → 닫기 → add_token(새 conn) → 또 새 conn UPDATE` 구조라 **원자성 0.** 동시 요청 두 번이면 출석 보상 2회 지급.
- 조치: 요청 스코프 세션 + `with transaction():` 컨텍스트 매니저로 통일.

### 16. 스케줄러

- `BackgroundScheduler` 가 앱 프로세스 내부 → **워커 N개면 N번 실행.** 토큰 만료 차감이 N중으로 걸림.
- `warn_expiring_silver_tokens()` 가 `token_type='silver'` 를 조회하는데 실제 저장값은 `'event'` → **영원히 0건.** 죽은 코드.
- `token_type` 값이 `event / purchased / use / expire / gold` 로 혼용 중 (purchases는 `'gold'`). Enum 으로 통일 필요.
- `check_anniversary_achievements()` 가 월-일만 비교 → 가입 당일에도 "1년 기념" 지급.
- 조치: 별도 워커 프로세스로 분리(또는 `--workers 1` 인스턴스 1대에만).

---

## P2 — 품질·운영

- **테스트 0개.** 최소한 토큰 차감/지급, 권한 경계(private·adult·타인 리소스)는 pytest 로 고정해야 재구성 중 회귀를 못 잡음.
- `requirements.txt` 가 **UTF-16LE** → Linux에서 `pip install -r` 즉시 실패. 배포 시도하면 여기서 막힘.
- `Dockerfile` / CI 없음. `venv/` 가 리포지토리 안에 존재.
- `models.py` 는 실제 스키마와 불일치하는 주석용 껍데기(`chat_history` 컬럼, `characters.category` 등). 삭제 대상.
- `char_id = f"custom_{name}_{uuid}"` → 한글·공백·특수문자가 PK와 URL에 들어감. UUID만 쓰고 이름은 컬럼으로.
- FE가 `access_token` 을 `localStorage` 에 저장 → 7번 XSS와 결합 시 계정 탈취. httpOnly 쿠키 + CSRF 토큰으로 이전 권장.
- Flutter도 `SharedPreferences` 에 토큰 평문 저장 → `flutter_secure_storage` 로 교체.
- API base URL이 ngrok 하드코딩(`api_service.dart:6`, `.env.production`, `main.py` CORS 3곳). 환경변수 1곳으로 통합.
- `chat/router.py` OOC 수정 시 메모리 캐시 갱신 로직이 `msg.get("id")` 를 보는데 히스토리에 `id` 를 넣은 적이 없음 → **항상 매칭 실패.** DB만 바뀌고 AI 컨텍스트는 옛 내용 유지.
- PDF export 의 `Content-Disposition` 에 한글 파일명 raw 삽입 → RFC 5987 (`filename*=UTF-8''...`) 필요.
- 회원 탈퇴가 `community_posts`·`community_comments`·`notifications`·`refresh_tokens`·`purchases` 를 남김. 개인정보 파기 의무 관점에서 정리 필요.

---

## 재구성 설계안

### 디렉터리 (라우터 단일 파일 → 레이어 분리)

```
backend/
  core/
    config.py        # pydantic-settings, env 필수값 강제 (fallback 금지)
    db.py            # engine, SessionLocal, get_db, transaction()
    security.py      # JWT (type 검증 포함), 해싱
    deps.py          # get_current_user / require_admin / require_adult
    errors.py        # 도메인 예외 → HTTP 매핑 핸들러
  domain/
    tokens/  {router.py, service.py, repository.py, schemas.py}
    chat/    {router.py, service.py, session_store.py, llm.py}
    characters/, users/, party/, community/, admin/ ...
  migrations/        # alembic
  tests/
```

- **router** = 검증·권한만. **service** = 트랜잭션 경계와 비즈니스 규칙. **repository** = 쿼리.
- 지금은 라우터가 세 역할을 다 하고 있어서 트랜잭션을 걸 자리가 없는 게 근본 원인.

### 권한 모델

```python
# core/deps.py
def require_character_access(char_id: str, user = Depends(get_current_user)):
    char = repo.get(char_id)
    if not char: raise NotFound
    if char.visibility == "private" and char.user_id != user.id: raise Forbidden
    if char.is_adult and not user.is_adult: raise Forbidden
    return char
```

- `/chat`, `/chat/resume`, `/chat/sessions`, `/chat/export`, 감정·배경 조회까지 전부 이 의존성을 타게 함. 지금은 각 라우터가 제각각 검사하거나 아예 안 함.

### 토큰 경제 (단일 원장 모델)

- `users.token_balance` / `token_purchased` / `token_event` 3중 관리 폐기.
- `token_ledger` 테이블 하나 + 잔액은 집계 또는 `users` 의 캐시 컬럼(트리거·서비스에서만 갱신).
- 모든 지급/차감은 `idempotency_key UNIQUE` 를 갖는 단일 서비스 함수 경유. 출석·광고·구매 중복 지급이 구조적으로 불가능해짐.
- 차감은 `SELECT ... FOR UPDATE` (MySQL 전환 후) 또는 조건부 UPDATE + rowcount 확인.

### 채팅 파이프라인

```
요청 → 권한 검사 → 토큰 홀드(예약 차감) → LLM 비동기 호출(SSE)
     → 성공 시 확정 / 실패 시 홀드 해제 → 히스토리 저장
```

- 현재는 차감 후 LLM 실패해도 롤백이 없어 유저 토큰이 증발.
- 세션 히스토리는 Redis(`chat:{user_id}:{session_id}`, TTL 2h) 로. 프로세스 메모리 dict 제거.

### 인프라

- NCP 서버 + Docker Compose (app / mysql / redis), Cloudflare 앞단(WAF·rate limit·SSL). ngrok 제거.
- 이미지: NCP Object Storage. 앱 서버가 `../frontend/images` 에 직접 쓰는 구조는 스케일아웃 불가.
- FE는 Cloudflare Pages 로 분리. 지금처럼 FastAPI가 `dist` 를 `StaticFiles` 로 마운트하면 배포가 묶임.

---

## 재개 순서 (권장)

| 단계 | 내용 | 기준 |
|---|---|---|
| 0 | 시크릿 회전 + git 히스토리에서 `.db`/`.env` 제거 + `.gitignore` UTF-8 재작성 | 반나절 |
| 1 | P0 1·3·4·6·7 패치 (결제 엔드포인트 차단, `/chat` 권한, 세션 키, JWT type, 업로드 ext) | 1~2일 |
| 2 | `core/` 도입 + 트랜잭션 컨텍스트 + 토큰 원장 재설계 + 회귀 테스트 | 3~5일 |
| 3 | MySQL + Alembic 전환, 인덱스 적용, 동기/비동기 정리 | 3~5일 |
| 4 | 파티챗 재작성 또는 제거, 모더레이션 큐, 본인확인 연동 | 별도 |
| 5 | Docker + NCP + Cloudflare 배포, CBT 재개 | 2~3일 |

- 1단계까지만 해도 "열어두면 털리는 상태"에서는 벗어남.
- 2~3단계가 실제 재구성이고, 여기서 미루면 유저 늘 때마다 같은 버그가 계속 재발.
