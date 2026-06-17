interface PrivacyPageProps {
  onBack: () => void;
}

export default function PrivacyPage({ onBack }: PrivacyPageProps) {
  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh", maxWidth: 720, margin: "0 auto", padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button
          onClick={onBack}
          style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
          }}
        >
          ←
        </button>
        <div style={{ fontSize: 22, fontWeight: 700 }}>개인정보처리방침</div>
      </div>

      <div className="glass-card" style={{ borderRadius: 24, padding: 32, display: "flex", flexDirection: "column", gap: 24, lineHeight: 1.8, color: "var(--text-secondary)", fontSize: 14 }}>
        <div style={{ color: "var(--text-muted)", fontSize: 13 }}>최종 수정일: 2026년 6월 17일</div>

        {[
          {
            title: "1. 수집하는 개인정보 항목",
            content: "• 필수 항목: 이메일, 비밀번호, 닉네임\n• 서비스 이용 과정에서 생성되는 정보: 대화 기록, 생성 캐릭터, 토큰 사용 내역, 접속 로그"
          },
          {
            title: "2. 개인정보 수집 및 이용 목적",
            content: "• 회원 가입 및 서비스 제공\n• AI 대화 서비스 운영\n• 서비스 개선 및 신규 서비스 개발\n• 법령 및 약관 위반 방지"
          },
          {
            title: "3. 개인정보 보유 및 이용 기간",
            content: "회원 탈퇴 시까지 보유합니다. 단, 관련 법령에 따라 일정 기간 보관이 필요한 경우 해당 기간 동안 보관합니다.\n• 전자상거래 기록: 5년\n• 접속 로그: 3개월"
          },
          {
            title: "4. 개인정보의 제3자 제공",
            content: "서비스는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다. 다만, 법령의 규정에 의거하거나 수사기관의 요청이 있는 경우는 예외로 합니다."
          },
          {
            title: "5. 개인정보 처리 위탁",
            content: "서비스는 AI 대화 서비스 운영을 위해 Google Gemini API를 활용합니다. 해당 서비스의 개인정보 처리방침은 Google의 정책을 따릅니다."
          },
          {
            title: "6. 이용자의 권리",
            content: "이용자는 언제든지 개인정보 열람, 정정, 삭제, 처리정지를 요청할 수 있습니다. 요청은 서비스 내 설정 메뉴 또는 고객센터를 통해 가능합니다."
          },
          {
            title: "7. 쿠키 사용",
            content: "서비스는 로그인 상태 유지를 위해 쿠키 및 로컬 스토리지를 사용합니다. 브라우저 설정을 통해 쿠키 저장을 거부할 수 있으나, 서비스 이용이 제한될 수 있습니다."
          },
          {
            title: "8. 개인정보 보호책임자",
            content: "개인정보 관련 문의는 서비스 내 고객센터를 통해 접수하실 수 있습니다."
          },
          {
            title: "9. 청소년 보호",
            content: "서비스는 만 14세 미만 아동의 개인정보를 수집하지 않습니다. 만 14세 미만인 경우 서비스 이용이 제한됩니다. 성인 전용 콘텐츠는 성인 인증을 통해서만 접근 가능합니다."
          },
        ].map((section, i) => (
          <div key={i}>
            <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)", marginBottom: 8 }}>
              {section.title}
            </div>
            <div style={{ whiteSpace: "pre-line" }}>{section.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}