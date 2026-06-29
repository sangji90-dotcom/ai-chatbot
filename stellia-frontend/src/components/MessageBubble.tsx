import type { Message } from "../App";

interface MessageBubbleProps {
  message: Message;
  characterName: string;
  emotionImageUrl?: string;  // 현재 감정 이미지 URL
}

export default function MessageBubble({ message, characterName, emotionImageUrl }: MessageBubbleProps) {
  const isUser = message.sender === "user";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", width: "100%" }}>
        <div style={{ maxWidth: "70%", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
          <div style={{
            padding: "14px 18px",
            borderRadius: "22px 22px 6px 22px",
            background: "linear-gradient(135deg, var(--primary), var(--primary-active))",
            color: "#fff", lineHeight: 1.6, fontSize: 15,
            boxShadow: "0 0 25px rgba(139,124,255,.35), 0 10px 30px rgba(0,0,0,.25)",
          }}>
            {message.content}
          </div>
          <span style={{ fontSize: 12, color: "var(--text-muted)", paddingRight: 4 }}>
            {message.timestamp}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", justifyContent: "flex-start", width: "100%" }}>
      <div style={{ display: "flex", gap: 12, alignItems: "flex-start", maxWidth: "75%" }}>
        {/* 아바타 */}
        <div style={{
          width: 42, height: 42, borderRadius: "50%",
          background: "var(--gradient-cosmic)",
          display: "grid", placeItems: "center",
          fontWeight: 700, fontSize: 16, flexShrink: 0,
          border: "2px solid rgba(139,124,255,.3)",
          boxShadow: "0 0 18px rgba(139,124,255,.22)",
        }}>
          {characterName[0]}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {/* 텍스트 버블 */}
          <div style={{
            padding: "16px 18px",
            borderRadius: "22px 22px 22px 6px",
            background: "linear-gradient(180deg, rgba(24,29,54,.95), rgba(17,21,40,.95))",
            border: "1px solid var(--border-default)",
            color: "var(--text-primary)", lineHeight: 1.7, fontSize: 15,
            backdropFilter: "blur(18px)",
          }}>
            {message.content}
          </div>

          {/* 감정 이미지 카드 — 이미지 있을 때만 */}
          {emotionImageUrl && (
            <div style={{
              borderRadius: 16, overflow: "hidden",
              border: "1px solid var(--border-default)",
              background: "rgba(17,21,40,.8)",
              maxWidth: 280,
              animation: "fadeInUp .3s ease",
            }}>
              <img
                src={emotionImageUrl}
                alt={characterName}
                style={{
                  width: "100%", display: "block",
                  objectFit: "cover", maxHeight: 320,
                }}
              />
              <div style={{
                padding: "8px 14px",
                color: "var(--text-muted)", fontSize: 12,
                textAlign: "center", letterSpacing: "0.05em",
              }}>
                [{characterName}]
              </div>
            </div>
          )}

          <span style={{ fontSize: 12, color: "var(--text-muted)", paddingLeft: 4 }}>
            {message.timestamp}
          </span>
        </div>
      </div>

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}