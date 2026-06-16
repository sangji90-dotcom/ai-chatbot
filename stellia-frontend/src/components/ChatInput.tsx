import { useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  characterName: string;
}

export default function ChatInput({ onSend, characterName }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const sendMessage = () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setMessage("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div
      style={{
        position: "relative",
        padding: "20px 24px 24px",
        borderTop: "1px solid var(--border-subtle)",
        background: "linear-gradient(to top, rgba(9,11,20,.95), rgba(17,21,40,.55))",
        backdropFilter: "blur(20px)",
      }}
    >
      <div
        className="chat-input-shell"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: 12,
          borderRadius: 24,
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.95), rgba(17,21,40,.95))",
          backdropFilter: "blur(18px)",
        }}
      >
        <button className="input-icon-btn">✦</button>

        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`${characterName}에게 메시지 보내기...`}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            background: "transparent",
            color: "var(--text-primary)",
            fontSize: 15,
          }}
        />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "10px 12px",
            borderRadius: 14,
            background: "rgba(246,198,91,.08)",
            border: "1px solid rgba(246,198,91,.15)",
            color: "var(--gold)",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ✦ 1
        </div>

        <button onClick={sendMessage} className="send-button">
          전송
        </button>
      </div>

      <style>{`
        .chat-input-shell { transition: all .2s ease; }
        .chat-input-shell:focus-within {
          border-color: var(--primary);
          box-shadow: 0 0 30px rgba(139,124,255,.18);
        }
        .input-icon-btn {
          width:42px; height:42px; border-radius:14px;
          border:1px solid var(--border-default);
          background:rgba(255,255,255,.02);
          color:var(--secondary); transition:all .2s ease;
        }
        .input-icon-btn:hover {
          border-color:var(--primary); color:white;
          box-shadow:0 0 20px rgba(139,124,255,.25);
        }
        .send-button {
          height:48px; min-width:80px; border:none;
          border-radius:16px; background:var(--gradient-cosmic);
          color:white; font-weight:700; transition:all .2s ease;
          box-shadow:0 0 25px rgba(139,124,255,.28);
        }
        .send-button:hover {
          transform:translateY(-1px);
          box-shadow:0 0 35px rgba(139,124,255,.4);
        }
      `}</style>
    </div>
  );
}