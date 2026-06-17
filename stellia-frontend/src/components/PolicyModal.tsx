interface PolicyModalProps {
  onAgree: () => void;
  onClose: () => void;
}

export default function PolicyModal({ onAgree, onClose }: PolicyModalProps) {
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.7)",
          backdropFilter: "blur(4px)",
        }}
      />
      <div
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 480, maxWidth: "92vw",
          maxHeight: "85vh",
          borderRadius: 28,
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(0,0,0,.5)",
          display: "flex", flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* 헤더 */}
        <div style={{ padding: "24px 24px 0", flexShrink: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 20, marginBottom: 8 }}>
            캐릭터 제작 시 반드시 유의해주세요!
          </div>
        </div>

        {/* 내용 */}
        <div style={{ overflowY: "auto", flex: 1, padding: "16px 24px" }}>
          <div style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.8, display: "flex", flexDirection: "column", gap: 16 }}>
            <p>
              안전하고 즐거운 대화 환경을 위해 Stellia 운영진은 실시간으로 모니터링하며,
              운영 정책 위반 시 캐릭터 삭제 및 계정 차단 조치를 취할 수 있습니다.
            </p>

            <div
              style={{
                padding: 16, borderRadius: 14,
                background: "rgba(255,107,138,.08)",
                border: "1px solid rgba(255,107,138,.2)",
              }}
            >
              <div style={{ fontWeight: 700, color: "#ff6b8a", marginBottom: 10 }}>⚠ 금지 사항</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {[
                  "과도한 선정성, 지나치게 공격적이거나 편향적인 표현",
                  "저작권, 초상권 등 타인의 권리를 침해하는 행위",
                  "딥페이크, 허위 정보, 미성년자 성적 대상화 등 비윤리적이거나 불법적인 행위",
                  "아동 성적 콘텐츠(로리, 쇼타 등) 생성 시도",
                  "특정 개인이나 단체를 비방하거나 혐오를 조장하는 콘텐츠",
                ].map((item, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <span style={{ color: "#ff6b8a", flexShrink: 0 }}>•</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div
              style={{
                padding: 16, borderRadius: 14,
                background: "rgba(139,124,255,.08)",
                border: "1px solid rgba(139,124,255,.2)",
              }}
            >
              <div style={{ fontWeight: 700, color: "var(--primary)", marginBottom: 10 }}>✦ 창작자 책임</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {[
                  "창작자는 본인이 만든 캐릭터의 콘텐츠에 대해 책임을 집니다.",
                  "타인의 캐릭터, 작품을 무단으로 사용하지 마세요.",
                  "유저가 제작한 캐릭터의 저작권은 창작자에게 귀속됩니다.",
                ].map((item, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <span style={{ color: "var(--primary)", flexShrink: 0 }}>•</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
              운영 정책을 반복적으로 위반할 경우, 제재 조치가 강화될 수 있습니다.
              캐릭터 제작을 계속하면 위 정책에 동의하는 것으로 간주됩니다.
            </p>
          </div>
        </div>

        {/* 버튼 */}
        <div style={{ padding: 20, flexShrink: 0, display: "flex", gap: 10 }}>
          <button
            onClick={onClose}
            style={{
              flex: 1, padding: "14px", borderRadius: 14,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", fontWeight: 600, cursor: "pointer",
            }}
          >
            취소
          </button>
          <button
            onClick={onAgree}
            style={{
              flex: 2, padding: "14px", borderRadius: 14, border: "none",
              background: "var(--gradient-cosmic)",
              color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer",
              boxShadow: "0 0 20px rgba(139,124,255,.3)",
            }}
          >
            동의하고 캐릭터 제작하기
          </button>
        </div>
      </div>
    </>
  );
}