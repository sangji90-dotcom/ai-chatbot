// src/components/MessageBubble.tsx

import type { Message } from "../App";

interface MessageBubbleProps {
message: Message;
avatar?: string;
}

export default function MessageBubble({
message,
avatar,
}: MessageBubbleProps) {
const isUser = message.sender === "user";

if (isUser) {
return (
<div
style={{
display: "flex",
justifyContent: "flex-end",
width: "100%",
}}
>
<div
style={{
maxWidth: "70%",
display: "flex",
flexDirection: "column",
alignItems: "flex-end",
gap: 6,
}}
>
<div
style={{
padding: "14px 18px",
borderRadius: "22px 22px 6px 22px",
background:
"linear-gradient(135deg, var(--primary), var(--primary-active))",
color: "#fff",
lineHeight: 1.6,
fontSize: 15,
boxShadow:
"0 0 25px rgba(139,124,255,.35), 0 10px 30px rgba(0,0,0,.25)",
border: "1px solid rgba(255,255,255,.08)",
backdropFilter: "blur(12px)",
}}
>
{message.content} </div>

      <span
        style={{
          fontSize: 12,
          color: "var(--text-muted)",
          paddingRight: 4,
        }}
      >
        {message.timestamp}
      </span>
    </div>
  </div>
);


}

return (
<div
style={{
display: "flex",
justifyContent: "flex-start",
width: "100%",
}}
>
<div
style={{
display: "flex",
gap: 12,
alignItems: "flex-end",
maxWidth: "75%",
}}
>
{avatar && (
<img
src={avatar}
alt=""
style={{
width: 42,
height: 42,
borderRadius: "50%",
objectFit: "cover",
border: "2px solid rgba(139,124,255,.3)",
boxShadow:
"0 0 18px rgba(139,124,255,.22), 0 0 35px rgba(95,214,255,.08)",
flexShrink: 0,
}}
/>
)}


    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      <div
        className="ai-message"
        style={{
          position: "relative",
          padding: "16px 18px",
          borderRadius: "22px 22px 22px 6px",
          background:
            "linear-gradient(180deg, rgba(24,29,54,.95), rgba(17,21,40,.95))",
          border: "1px solid var(--border-default)",
          color: "var(--text-primary)",
          lineHeight: 1.7,
          fontSize: 15,
          backdropFilter: "blur(18px)",
          boxShadow:
            "0 12px 30px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.03)",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "inherit",
            background:
              "linear-gradient(135deg, rgba(139,124,255,.03), rgba(95,214,255,.02))",
            pointerEvents: "none",
          }}
        />

        <div
          style={{
            position: "relative",
            zIndex: 1,
          }}
        >
          {message.content}
        </div>
      </div>

      <span
        style={{
          fontSize: 12,
          color: "var(--text-muted)",
          paddingLeft: 4,
        }}
      >
        {message.timestamp}
      </span>
    </div>
  </div>

  <style>
    {`
    .ai-message:hover{
      border-color: var(--primary);
      box-shadow:
        0 0 30px rgba(139,124,255,.12),
        0 10px 30px rgba(0,0,0,.25);
    }
    `}
  </style>
</div>


);
}
