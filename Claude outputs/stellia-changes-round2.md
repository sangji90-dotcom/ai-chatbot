# Stellia 2차 작업 (2026-09-16)

검증: **pytest 43개 통과**(24 → 43), `compileall` 통과, 실 `.env` 기동 성공(라우트 149개), FE `tsc` 에러 0.

---

## 가장 중요한 것 — FK를 켜니 파티챗이 이미 죽어 있었다

1차에서 `PRAGMA foreign_keys=ON`을 켰는데, 정합성 점검 스크립트를 돌려보니 **실제 DB에 FK 위반 15건**이 있었다. 원인을 파보니:

```sql
-- party_members 의 실제 FK 정의
FOREIGN KEY (room_id) REFERENCES "party_rooms_old"(id)   -- ← 이 테이블은 존재하지 않음
```

`_migrate_party_rooms_nullable()` 이 `ALTER TABLE party_rooms RENAME TO party_rooms_old` 를 실행했는데, **SQLite 3.25+ 는 이때 자식 테이블의 FK 참조명까지 같이 바꾼다.** 그리고 그 `party_rooms_old` 는 곧바로 DROP 됐다.

지금까지는 FK가 꺼져 있어서 드러나지 않았지만, 켜는 순간:

```
INSERT INTO party_members ... → OperationalError: no such table: main.party_rooms_old
```

**방 만들기·입장이 전부 실패한다.** 재현 테스트로 확인했고, `_repair_dangling_fk_references()` 마이그레이션을 추가해 `party_members` / `party_messages` 를 올바른 FK로 재생성하도록 했다. 고아 행(존재하지 않는 캐릭터를 참조하던 party_rooms 4건)도 함께 정리. 실DB 사본 적용 후 정합성 점검 통과 + 방 생성/입장 테스트 통과.

---

## 1차에서 못 본 라우터 8개 감사 결과

### 배너 — 관리자 검사가 아예 없었다

```python
@router.post("", summary="배너 등록 (관리자)")   # summary 에만 "(관리자)"
async def create_banner(..., current_user = Depends(get_current_user)):   # is_admin 검사 없음
```

로그인한 **아무나** 메인 배너를 등록·삭제·토글할 수 있었다. `link_url` 이 자유 입력이라 **메인 화면에 피싱 링크를 띄울 수 있는 경로.**
→ 3개 엔드포인트 전부 `require_admin`, URL 스킴 화이트리스트(`javascript:` 차단) 추가.

### 캐릭터 prompt 유출 + private 캐릭터 노출

- `/likes/me`, `/likes/bookmarks`, `/follows/me/new-characters` 가 전부 `SELECT c.*` → **캐릭터 `prompt`(제작자 핵심 자산)가 응답에 그대로** 나갔다.
- `/follows/me/new-characters` 는 공개/성인 필터도 없어 **팔로우만 하면 남의 private 캐릭터를 prompt까지 조회** 가능했다.
→ `core/serializers.py` 신설(prompt는 소유자에게만), 목록 쿼리에 공개 필터, 좋아요·북마크에 `assert_character_access()`.

### 무인증 Gemini 호출 2곳

`POST /support/ask`, `POST /support/inquiries` 가 인증도 레이트리밋도 없었다. 이 엔드포인트만으로 API 비용 공격이 가능.
→ 인증 필수 + 비동기 호출로 전환. `/suggestions` 도 인증 필수(스팸 차단 수단이 없었음).

### 커넥션 누수 4곳

`likes/router.py` 의 북마크 엔드포인트 4개가 전부 `conn.close()` 없음. 캐릭터 존재 확인도 없었음.
→ 라우터 전체를 `transaction()` / `read_only()` 로 재작성.

### 기타

- **커뮤니티에 댓글 수정/삭제 API가 아예 없었다** (FE엔 수정·삭제 UI가 있음) → 추가
- 커뮤니티 목록이 `is_adult` 컬럼을 두고도 안 써서 **성인 게시글이 미성년 계정에 그대로 노출** → 필터 추가
- 남의 **private 캐릭터를 게시글에 태그**해 이름·이미지를 노출시킬 수 있었음 → 공개 여부 확인
- 커뮤니티 목록 N+1 (20개 조회에 41쿼리) → IN 절 2쿼리로
- `achievements.check_and_grant()` 의 확인↔INSERT 경합 → `INSERT OR IGNORE` + rowcount 판정으로 원자화, 보상 지급도 같은 트랜잭션
- 리뷰: 대화 이력 없는 계정의 평점 조작 차단, 비공개 캐릭터 리뷰 차단
- Vision 분석이 동기 호출이라 이벤트 루프를 막던 것 + png/gif를 `image/jpeg`로 보내던 것 수정
- `bare except:` 제거(팔로우·좋아요가 모든 오류를 "이미 팔로우함"으로 삼키고 있었음)
- 길이/타입 검증: 게시글 5000자, 댓글 1000자, 문의 4000자, 파티 인원 2~10 등

---

## 추가한 것

### Redis 백엔드 (자동 폴백)

`REDIS_URL` 만 넣으면 세션 캐시와 레이트리밋이 공유 저장소로 전환된다. **Redis가 없거나 죽으면 자동으로 인메모리 폴백** — 연결 실패로 서비스가 멈추지 않는다(죽은 주소로 테스트 확인). 워커를 2개 이상 띄우는 시점에 필요.

### CI (`.github/workflows/ci.yml`)

- backend: pytest + **시크릿 스캔**(`.env`·`.db` 가 추적되면 빌드 실패)
- frontend: `tsc --noEmit` + `vite build`
- flutter: `flutter analyze`

### 운영 스크립트

| 스크립트 | 용도 |
|---|---|
| `scripts/backup_db.py` | WAL 안전 온라인 백업(`cp` 는 깨진 사본이 나온다) + gzip + 보관기간 관리 |
| `scripts/check_integrity.py` | 토큰 잔액 drift·음수 토큰·고아 행·FK 위반 점검. **이 스크립트가 위 파티챗 버그를 찾아냈다** |
| `scripts/make_admin.py` | 최초 관리자 지정 (권한 부여 API는 관리자만 호출 가능해서 부트스트랩 불가였음) |

### 관측성

- 요청마다 `X-Request-ID` 발급 → 로그와 500 응답 body에 동일 ID (사용자 문의 ↔ 로그 대조 가능). 로그인/회원가입 본문은 로깅 제외
- `/health` 에 DB 프로브 추가 — 프로세스만 살고 DB가 죽은 상태를 정상으로 보고하지 않음(503)

### `backend/README.md`

실행법·환경변수 표·구조 설명 + **지켜야 할 규칙 5가지**(DB는 `core.db` 경유, 토큰은 `token_service`만, 캐릭터 접근은 `assert_character_access`, `SELECT c.*` 금지, LLM은 `await llm.generate`). 다음에 기능 추가할 때 같은 구멍이 다시 생기는 걸 막는 용도.

---

## 테스트 43개

| 파일 | 내용 |
|---|---|
| `test_security.py` | 결제 권한·`/chat` 인증·private 차단·refresh 우회·미성년 캐릭터·비밀번호 정책·레이트리밋 |
| `test_tokens.py` | 잔액 정합성·음수 방지·멱등성·**동시 차감 10스레드**·중복 출석 |
| `test_router_permissions.py` | 배너 권한·prompt 유출·private 좋아요/북마크/팔로우피드·무인증 LLM·리뷰 조작·댓글 권한·private 태그 |
| `test_migration.py` | **깨진 FK 재현 → 복구 검증** + 방 생성/입장 |
| `test_cache_fallback.py` | Redis 없이도 세션·레이트리밋 정상 동작 |
| `test_upload.py` | GIF polyglot 확장자 판정 |
| `test_session_isolation.py` | 세션 키 유저 분리 |

---

## 남은 것 (형 결정이 필요)

| 항목 | 막힌 지점 |
|---|---|
| PG 연동 | 사업자등록. 그 전까지 지급은 관리자 전용 |
| 광고 SSV | 광고 SDK 선택 (AdMob/유니티 등). 현재는 일일 한도가 유일한 방어선 |
| 본인확인 | PASS/NICE 계약. 그 전까지 production 성인인증 비활성 |
| **비밀번호 재설정** | FAQ엔 "비밀번호 찾기"가 안내돼 있는데 **API가 없다.** 메일 발송 수단(SES/센드그리드/네이버웍스)만 정하면 구현 가능 |
| MySQL 전환 | NCP 인스턴스·접속정보 |
| Redis 실제 기동 | `REDIS_URL` 만 넣으면 됨 (코드는 준비됨) |
