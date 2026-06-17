interface LoginPromptModalProps {
  onClose: () => void;
  onLogin: () => void;
  onRegister: () => void;
}

export default function LoginPromptModal({ onClose, onLogin, onRegister }: LoginPromptModalProps) {
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.6)",
          backdropFilter: "blur(4px)",
        }}
      />
      <div
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 380, maxWidth: "90vw",
          borderRadius: 28,
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(0,0,0,.5), 0 0 30px rgba(139,124,255,.1)",
          padding: 32,
          display: "flex", flexDirection: "column", alignItems: "center", gap: 20,
        }}
      >
        {/* 아이콘 */}
        <div
          style={{
            width: 72, height: 72, borderRadius: "50%",
            background: "var(--gradient-cosmic)",
            display: "grid", placeItems: "center",
            fontSize: 32,
            boxShadow: "var(--shadow-glow-primary)",
          }}
        >
          ✦
        </div>

        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
            대화를 시작하려면 로그인이 필요해요
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6 }}>
            Stellia에 가입하고 다른 세계의 캐릭터들과 대화해보세요.
            무료로 시작할 수 있어요!
          </div>
        </div>

        <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 10 }}>
          <button
            onClick={onRegister}
            style={{
              width: "100%", padding: "14px", borderRadius: 14, border: "none",
              background: "var(--gradient-cosmic)",
              color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer",
              boxShadow: "0 0 20px rgba(139,124,255,.3)",
            }}
          >
            무료로 회원가입하기
          </button>
          <button
            onClick={onLogin}
            style={{
              width: "100%", padding: "14px", borderRadius: 14,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-secondary)", fontWeight: 600, fontSize: 15, cursor: "pointer",
            }}
          >
            이미 계정이 있어요
          </button>
        </div>

        <button
          onClick={onClose}
          style={{
            background: "none", border: "none",
            color: "var(--text-muted)", fontSize: 13, cursor: "pointer",
          }}
        >
          나중에 하기
        </button>
      </div>
    </>
  );
}