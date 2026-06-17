interface TermsPageProps {
  onBack: () => void;
}

export default function TermsPage({ onBack }: TermsPageProps) {
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
        <div style={{ fontSize: 22, fontWeight: 700 }}>이용약관</div>
      </div>

      <div className="glass-card" style={{ borderRadius: 24, padding: 32, display: "flex", flexDirection: "column", gap: 24, lineHeight: 1.8, color: "var(--text-secondary)", fontSize: 14 }}>
        <div style={{ color: "var(--text-muted)", fontSize: 13 }}>최종 수정일: 2026년 6월 17일</div>

        {[
          {
            title: "제1조 (목적)",
            content: "본 약관은 Stellia(이하 '서비스')가 제공하는 AI 캐릭터 챗봇 서비스의 이용과 관련하여 서비스와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다."
          },
          {
            title: "제2조 (정의)",
            content: "'서비스'란 Stellia가 제공하는 AI 캐릭터 대화 서비스를 의미합니다. '이용자'란 본 약관에 동의하고 서비스를 이용하는 자를 의미합니다. '창작자'란 서비스 내에서 AI 캐릭터를 제작하는 이용자를 의미합니다."
          },
          {
            title: "제3조 (약관의 효력 및 변경)",
            content: "본 약관은 서비스 화면에 게시하거나 이용자에게 공지함으로써 효력이 발생합니다. 서비스는 합리적인 사유가 있을 경우 약관을 변경할 수 있으며, 변경 시 사전 공지합니다."
          },
          {
            title: "제4조 (이용자의 의무)",
            content: "이용자는 서비스 이용 시 다음 행위를 해서는 안 됩니다.\n• 미성년자 성적 콘텐츠(로리, 쇼타 등) 생성 및 요청\n• 타인의 저작권, 초상권 침해\n• 허위 정보 유포 및 타인 사칭\n• 서비스의 안정적 운영을 방해하는 행위\n• 과도한 선정성, 혐오 표현 등 불법 콘텐츠 생성"
          },
          {
            title: "제5조 (서비스 이용 제한)",
            content: "서비스는 이용자가 본 약관 및 운영 정책을 위반할 경우 사전 통보 없이 서비스 이용을 제한하거나 계정을 정지할 수 있습니다."
          },
          {
            title: "제6조 (콘텐츠 저작권)",
            content: "이용자가 서비스 내에서 창작한 캐릭터 및 콘텐츠의 저작권은 창작자에게 귀속됩니다. 단, 서비스는 서비스 운영 및 홍보 목적으로 해당 콘텐츠를 활용할 수 있습니다."
          },
          {
            title: "제7조 (AI 생성 콘텐츠 면책)",
            content: "서비스의 AI가 생성하는 콘텐츠는 이용자의 입력에 의해 생성되며, 서비스는 AI 생성 콘텐츠의 정확성, 완전성, 적절성을 보장하지 않습니다. AI 생성 콘텐츠로 인한 분쟁에 대해 서비스는 책임을 지지 않습니다."
          },
          {
            title: "제8조 (럭키코인 및 결제)",
            content: "럭키코인은 서비스 내 가상 화폐로 현금으로 환전되지 않습니다. 구매한 럭키코인(금화)은 관련 법령이 허용하는 범위 내에서 환불이 가능합니다. 이벤트로 지급된 럭키코인(은화)은 환불되지 않습니다."
          },
          {
            title: "제9조 (면책 조항)",
            content: "서비스는 천재지변, 서버 장애, 기타 불가항력적 사유로 인한 서비스 중단에 대해 책임을 지지 않습니다."
          },
          {
            title: "제10조 (분쟁 해결)",
            content: "서비스 이용과 관련한 분쟁은 대한민국 법률을 준거법으로 하며, 관할 법원은 서울중앙지방법원으로 합니다."
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