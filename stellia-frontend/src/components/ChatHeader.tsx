// src/components/ChatHeader.tsx

import type { Character } from "../App";

interface ChatHeaderProps {
character: Character;
}

export default function ChatHeader({
character,
}: ChatHeaderProps) {
return (
<header
style={{
position: "relative",
zIndex: 3,
height: 88,
display: "flex",
alignItems: "center",
justifyContent: "space-between",
padding: "0 28px",
borderBottom: "1px solid var(--border-subtle)",
backdropFilter: "blur(20px)",
background:
"linear-gradient(to bottom, rgba(17,21,40,.85), rgba(17,21,40,.55))",
}}
>
{/* Left */}
<div
style={{
display: "flex",
alignItems: "center",
gap: 16,
}}
>
<div
style={{
position: "relative",
}}
>
<img
src={character.avatar}
alt={character.name}
style={{
width: 56,
height: 56,
borderRadius: "50%",
objectFit: "cover",
border: "2px solid var(--primary)",
boxShadow:
"0 0 20px rgba(139,124,255,.35), 0 0 40px rgba(95,214,255,.12)",
}}
/>


      {character.online && (
        <span
          style={{
            position: "absolute",
            right: 2,
            bottom: 2,
            width: 12,
            height: 12,
            borderRadius: "50%",
            background: "#41D980",
            border: "2px solid var(--bg-base)",
            boxShadow: "0 0 10px #41D980",
          }}
        />
      )}
    </div>

    <div>
      <div
        style={{
          fontSize: 20,
          fontWeight: 700,
          color: "var(--text-primary)",
        }}
      >
        {character.name}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginTop: 4,
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#41D980",
          }}
        />

        <span
          style={{
            color: "var(--text-secondary)",
            fontSize: 14,
          }}
        >
          {character.title}
        </span>
      </div>
    </div>
  </div>

  {/* Right Actions */}
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 12,
    }}
  >
    <ActionButton icon="♡" />
    <ActionButton icon="✦" />
    <ActionButton icon="⋯" />
  </div>
</header>


);
}

function ActionButton({
icon,
}: {
icon: string;
}) {
return (
<button
style={{
width: 44,
height: 44,
borderRadius: 14,
border: "1px solid var(--border-default)",
background: "rgba(24,29,54,.75)",
color: "var(--text-secondary)",
fontSize: 18,
transition: "all .2s ease",
backdropFilter: "blur(12px)",
}}
onMouseEnter={(e) => {
e.currentTarget.style.borderColor = "var(--primary)";
e.currentTarget.style.color = "var(--text-primary)";
e.currentTarget.style.boxShadow =
"0 0 20px rgba(139,124,255,.25)";
}}
onMouseLeave={(e) => {
e.currentTarget.style.borderColor = "var(--border-default)";
e.currentTarget.style.color = "var(--text-secondary)";
e.currentTarget.style.boxShadow = "none";
}}
>
{icon} </button>
);
}
