# Stellia

AI 캐릭터 챗봇 서비스. 사용자가 직접 AI 캐릭터를 만들고, 채팅하고, 커뮤니티에서 공유할 수 있는 플랫폼입니다.

> Meet Fate. Beyond Worlds.

## 프로젝트 구조
ai-chatbot/
├── backend/          # FastAPI 백엔드
├── stellia-frontend/ # React + TypeScript 웹 프론트엔드
└── stellia_app/       # Flutter Android 앱

## 기술 스택

**백엔드**
- FastAPI / Python 3.14
- SQLite (CBT 단계, 추후 PostgreSQL 이전 예정)
- Google Gemini 2.5 Flash (대화 생성, 캐릭터 자동완성)
- JWT 인증 (access + refresh token)

**웹 프론트엔드**
- React 19 + TypeScript + Vite
- React Router (클라이언트 사이드 라우팅)
- Axios

**모바일**
- Flutter (Android)
- Dio, SharedPreferences, image_picker

## 주요 기능

- AI 캐릭터 생성 및 채팅 (감정/상황별 이미지 전환)
- 캐릭터 자동완성 (AI 기반)
- 파티챗 (다중 유저 실시간 채팅, WebSocket)
- 커뮤니티 (게시글, 댓글, 좋아요, 캐릭터 태그, AI 이미지 자동분류)
- 토큰 경제 (금화/은화, 출석체크, 광고시청)
- 업적 및 칭호 시스템
- 메모리 시스템 (장기 대화 맥락 유지)
- 관리자 패널

## 개발 환경 설정

### 백엔드

```bash
cd backend
pip install -r requirements.txt --break-system-packages
uvicorn main:app --reload
```

`.env` 파일 필요:
GEMINI_API_KEY=...
JWT_SECRET=...
ENV=development

### 웹 프론트엔드

```bash
cd stellia-frontend
npm install
npm run dev
```

환경변수 (`.env.development` / `.env.production`):
VITE_API_URL=http://localhost:8000

### Flutter (Android)

```bash
cd stellia_app
flutter pub get
flutter emulators --launch Pixel_8
flutter run
```

## 보안

- Rate Limiting (엔드포인트별 차등 적용)
- XSS 필터링 미들웨어
- 이미지 업로드 매직바이트 검증
- JWT 자동 갱신 (axios interceptor)
- CORS 화이트리스트

## 로드맵

- [ ] SQLite → PostgreSQL 마이그레이션
- [ ] Railway 배포
- [ ] 토스페이먼츠 PG 연동
- [ ] 휴대폰 본인인증 (현재 자기선언 방식)
- [ ] Runpod + Stable Diffusion 이미지 생성
- [ ] Flutter iOS 지원

## 라이선스

비공개 프로젝트