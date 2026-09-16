# Stellia 재구성 적용 내역 (2026-09-16)

검증: **pytest 24개 전부 통과**, `compileall` 통과, 실제 `.env` 로 앱 기동 성공(라우트 147개), FE `tsc --noEmit` 에러 0.
작업 전 스냅샷은 세션에 보관(`pre-refactor-20260916-0534.tgz`) — `git diff` 로 전체 변경 확인 가능.

---

## 먼저 확인할 것 2가지

**1. `CreateCharacterPage.tsx` 가 깨져 있었음 (커밋 안 된 상태)**
파일 안에 `export default function CharacterProfileModal` 이 들어 있었음. 에디터 저장 사고로 보임.
→ **FE가 빌드 자체가 안 되는 상태였음.** `git checkout HEAD --` 로 정상 버전(518줄) 복구.

**2. 예전 GEMINI_API_KEY 가 git 히스토리에 남아 있음**
초기 커밋 `b9251e7` 에 `backend/.env` 가 통째로 들어갔고 `b617c4a` 에서 추적만 해제됨 → 히스토리에는 그대로 존재.
현재 쓰는 키와는 **다른 값**이라 지금 키는 안전하지만, **그 옛날 키는 Google AI Studio 에서 폐기**할 것.
`JWT_SECRET` 은 히스토리에 없었음.

---

## P0 — 치명적 취약점

| 항목 | 변경 |
|---|---|
| 결제 검증 없는 토큰 지급 | `POST /tokens/purchase/{id}`, `/purchases/manual`, `/tokens/memory-pass/purchase-cash` → **전부 `require_admin` 뒤로**. FE 결제 버튼은 "준비 중" 안내로 교체 |
| 토큰 잔액 drift | `token_balance` 를 `purchased+event` 파생값으로만 갱신. 앱 기동 시 기존 불일치 자동 복구 — **실DB 사본 테스트: 2건 → 0건** |
| 이중 차감 / 무료 채팅 | `deduct()` 를 조건부 단일 UPDATE + rowcount 검사로 원자화. 스레드 10개 동시 차감 테스트 통과 |
| 중복 지급 | `token_grants(idempotency_key)` 테이블 신설. 출석·광고·구매·초대·연속보상 전부 멱등키 경유 |
| `/chat` 무인증 | `get_optional_user` → **`get_current_user`**. 비로그인 Gemini 호출 차단 |
| `/chat` 권한 검사 누락 | `assert_character_access()` 신설 — private / 성인 캐릭터 검사를 한 곳으로. `/chat`, `/resume`, `/export` 에 적용 |
| 세션 캐시 크로스 유저 | 키를 `{user_id}:{session_id}:{character_id}` 로. TTL 2h + LRU 500 상한 (메모리 누수도 함께 해결) |
| refresh 토큰 우회 | `decode_token(token, expected_type="access")` — 30일 토큰으로 API 호출 불가 |
| JWT_SECRET | fallback 제거 + 32자 미만이면 기동 거부. **기존 14자였음 → 64자 hex 로 회전** (기존 로그인 세션은 전부 만료됨) |
| 업로드 polyglot XSS | 확장자를 magic bytes 판정 결과로 **서버가 결정**. 캐릭터/감정/배경/프로필/커뮤니티 5곳 전부 |
| 인증 없는 엔드포인트 | `DELETE /chat/{session}/{char}`, `POST /chat/new/{char}` 에 인증 추가 |

---

## P1 — 구조

- **`core/` 레이어 신설**: `config.py`(필수 env 강제·절대경로 DB) / `db.py`(`transaction()` 컨텍스트) / `security.py` / `token_service.py` / `middleware.py`
- **동시성**: Gemini 호출을 `chat/llm.py` 로 분리해 `client.aio` 비동기 경로 강제(없으면 `asyncio.to_thread`). DB 라우터는 `def` 로 전환해 threadpool 사용
- **LLM 실패 시 토큰 환급**: 차감 후 생성 실패하면 `refund()`. 기존엔 오류마다 유저 토큰이 증발
- **인덱스 17개 추가**: `chat_history` 3개 포함(기존 0개) + `token_history`, `characters`, `party_*`, `notifications` 등
- **FK 실제 작동**: 커넥션마다 `PRAGMA foreign_keys=ON` + WAL + busy_timeout. 캐릭터 삭제 시 연관 11개 테이블 정리
- **커넥션 누수**: `transaction()` / `read_only()` 로 예외 경로에서도 반드시 반납
- **미들웨어**: XFF 무조건 신뢰 → `TRUSTED_PROXY=cloudflare` 일 때만 `CF-Connecting-IP`. rate limit 버킷 만료(누수 해결), `/characters/auto-complete` 등 LLM 경로 규칙 추가. 전체 body XSS 정규식 제거(오탐+우회 둘 다 있었음) → CSP·nosniff·HSTS 헤더로 대체
- **파티챗 실동작**: `RoomManager` 추가로 브로드캐스트 + `party_messages` 저장 + `GET /party/rooms/{code}/messages`. 기존엔 본인에게만 에코라 기능이 없었음
- **스케줄러**: `token_type='silver'` 로 조회해 항상 0건이던 경고 잡 수정, 가입 당일 "1년 업적" 수정, `max_instances=1`, `RUN_SCHEDULER=0` 로 워커 중복 실행 차단
- **미성년 캐릭터 차단**: `age >= 19` 서버 검증 + Gemini safety settings + 유해 키워드 정규식(띄어쓰기·자모 우회 대응)
- **성인 인증**: 자기선언 방식은 `ENV=production` 에서 503. 본인확인 연동 전까지 봉인
- **멀티 디바이스**: 로그인 시 refresh 토큰 전부 삭제 → 최근 4개 유지. 웹 로그인하면 앱이 튕기던 문제 해소
- **OOC 수정 버그**: 캐시에 없는 `msg["id"]` 로 매칭해 항상 실패하던 것 수정(이제 AI 컨텍스트에도 반영)

---

## P2 — 품질·운영

- **테스트 24개 신설**: 권한 경계 / 토큰 정합성 / 동시 차감 / 멱등성 / 업로드 판정 / 세션 격리 / 레이트리밋
- `requirements.txt` UTF-16 → **UTF-8** (Linux `pip install -r` 이 여기서 막혔었음). `.gitignore` 도 동일
- `chatbot.db`(bcrypt 해시 포함) · FE `.env.*` **추적 해제**. 루트 0바이트 유령 DB 삭제
- `Dockerfile` + `docker-compose.yml` 신설 (app / scheduler 분리, 비루트, healthcheck)
- 비밀번호 정책(8자 이상 + 영문·숫자 혼용), 이메일 `EmailStr` 검증
- 전역 예외 핸들러 — 스택트레이스 유출 차단, `/health` 추가
- PDF 파일명 RFC 5987 인코딩, `char_id` 에서 한글·특수문자 제거
- 회원 탈퇴 시 남던 11개 테이블 정리 + 게시글/댓글 익명화
- **Flutter**: 토큰을 `SharedPreferences` 평문 → `flutter_secure_storage`(Keystore/Keychain), 기존 설치분 자동 마이그레이션. ngrok 하드코딩 → `--dart-define=API_BASE_URL`. Dio 인터셉터로 401 자동 갱신

---

## 지금 해야 할 일

```bash
# 1) 백엔드
cd backend
pip install -r requirements.txt     # redis/pytest/email-validator 추가됨
pytest                              # 24 passed 확인
uvicorn main:app --reload

# 2) 프론트
cd stellia-frontend && npm run build

# 3) Flutter
cd stellia_app && flutter pub get   # flutter_secure_storage 추가됨
flutter run --dart-define=API_BASE_URL=https://<서버주소>
```

주의: JWT_SECRET 을 회전했으므로 **기존 로그인 세션은 전부 만료**된다. 재로그인 필요.

---

## 손대지 않은 것 (판단이 필요해서)

| 항목 | 이유 |
|---|---|
| MySQL 전환 | NCP 인스턴스·접속정보가 필요. SQLite 상태에서 WAL·인덱스·FK 로 최대한 끌어올려 둠 |
| Redis 세션 | `chat/session_store.py` 만 교체하면 되게 인터페이스를 맞춰 둠 |
| localStorage → httpOnly 쿠키 | 백엔드·React·Flutter 세 곳의 인증 방식이 동시에 바뀜. 업로드 XSS 차단 + CSP 로 공격면은 줄여 둠 |
| PG 연동 | 사업자등록 선행. `purchases/router.py` 하단에 webhook 검증 4단계를 주석으로 명시 |
| 광고 SSV | 광고 SDK 선택 후. 현재는 일일 한도가 유일한 방어선 |
| 라우터 → service/repository 분리 | 전면 리팩터링. 트랜잭션 경계가 필요한 곳(토큰·채팅·파티)은 이미 분리 완료 |
