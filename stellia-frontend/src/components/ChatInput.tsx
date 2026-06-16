// src/components/ChatInput.tsx

import { useState } from "react";

interface ChatInputProps {
onSend: (message: string) => void;
}

export default function ChatInput({
onSend,
}: ChatInputProps) {
const [message, setMessage] = useState("");

const sendMessage = () => {
const trimmed = message.trim();


if (!trimmed) return;

onSend(trimmed);
setMessage("");


};

const handleKeyDown = (
  e: React.KeyboardEvent<HTMLInputElement>
) => {
  if (e.key === "Enter") {
    sendMessage();
  }
};

return (
<div
style={{
position: "relative",
padding: "20px 24px 24px",
borderTop: "1px solid var(--border-subtle)",
background:
"linear-gradient(to top, rgba(9,11,20,.95), rgba(17,21,40,.55))",
backdropFilter: "blur(20px)",
}}
>
{/* Glow */}
<div
style={{
position: "absolute",
left: "50%",
top: 0,
transform: "translateX(-50%)",
width: 300,
height: 1,
background:
"linear-gradient(90deg, transparent, rgba(139,124,255,.6), transparent)",
}}
/>


  <div
    className="chat-input-shell"
    style={{
      display: "flex",
      alignItems: "center",
      gap: 14,
      padding: 12,
      borderRadius: 24,
      border: "1px solid var(--border-default)",
      background:
        "linear-gradient(180deg, rgba(24,29,54,.95), rgba(17,21,40,.95))",
      backdropFilter: "blur(18px)",
      boxShadow:
        "0 12px 40px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.03)",
    }}
  >
    {/* Attachment */}
    <button
      className="input-icon-btn"
      aria-label="Attachment"
    >
      ✦
    </button>

    {/* Input */}
    <input
      value={message}
      onChange={(e) => setMessage(e.target.value)}
      onKeyDown={handleKeyDown}
      placeholder="Ask the stars a question..."
      style={{
        flex: 1,
        border: "none",
        outline: "none",
        background: "transparent",
        color: "var(--text-primary)",
        fontSize: 15,
      }}
    />

    {/* Coin Hint */}
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

    {/* Send */}
    <button
      onClick={sendMessage}
      className="send-button"
    >
      <span>Send</span>
    </button>
  </div>

  <style>
    {`
    .chat-input-shell{
      transition: all .2s ease;
    }

    .chat-input-shell:focus-within{
      border-color: var(--primary);
      box-shadow:
        0 0 30px rgba(139,124,255,.18),
        0 12px 40px rgba(0,0,0,.28);
    }

    .input-icon-btn{
      width:42px;
      height:42px;
      border-radius:14px;
      border:1px solid var(--border-default);
      background:rgba(255,255,255,.02);
      color:var(--secondary);
      transition:all .2s ease;
    }

    .input-icon-btn:hover{
      border-color:var(--primary);
      color:white;
      box-shadow:
        0 0 20px rgba(139,124,255,.25);
    }

    .send-button{
      height:48px;
      min-width:120px;
      border:none;
      border-radius:16px;
      background:var(--gradient-cosmic);
      color:white;
      font-weight:700;
      letter-spacing:.02em;
      transition:all .2s ease;
      box-shadow:
        0 0 25px rgba(139,124,255,.28);
    }

    .send-button:hover{
      transform:translateY(-1px);
      box-shadow:
        0 0 35px rgba(139,124,255,.4),
        0 8px 25px rgba(0,0,0,.25);
    }

    .send-button:active{
      transform:scale(.98);
    }

    @media (max-width:640px){

      .send-button{
        min-width:90px;
      }
    }
    `}
  </style>
</div>


);
}
