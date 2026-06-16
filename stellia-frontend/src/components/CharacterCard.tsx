// src/components/CharacterCard.tsx

import type { Character } from "../App";

interface CharacterCardProps {
character: Character;
active?: boolean;
}

export default function CharacterCard({
character,
active = false,
}: CharacterCardProps) {
return (
<button
className="character-card"
style={{
width: "100%",
textAlign: "left",
border: active
? "1px solid var(--primary)"
: "1px solid var(--border-default)",
background: active
? "linear-gradient(135deg, rgba(139,124,255,.18), rgba(95,214,255,.08))"
: "rgba(17,21,40,.65)",
borderRadius: 20,
padding: 14,
display: "flex",
gap: 14,
alignItems: "center",
transition: "all .2s ease",
backdropFilter: "blur(16px)",
boxShadow: active
? "var(--shadow-glow-primary)"
: "0 8px 24px rgba(0,0,0,.18)",
}}
>
<div
style={{
position: "relative",
flexShrink: 0,
}}
>
<img
src={character.avatar}
alt={character.name}
style={{
width: 58,
height: 58,
borderRadius: "50%",
objectFit: "cover",
border: active
? "2px solid var(--primary)"
: "2px solid var(--border-default)",
boxShadow: active
? "0 0 25px rgba(139,124,255,.45)"
: "none",
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
          border: "2px solid var(--bg-surface)",
          boxShadow: "0 0 10px #41D980",
        }}
      />
    )}
  </div>

  <div
    style={{
      flex: 1,
      minWidth: 0,
    }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div
        style={{
          fontWeight: 700,
          color: "var(--text-primary)",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {character.name}
      </div>
    </div>

    <div
      style={{
        marginTop: 4,
        color: "var(--text-secondary)",
        fontSize: 13,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
    >
      {character.title}
    </div>

    <div
      style={{
        marginTop: 8,
        display: "flex",
        alignItems: "center",
        gap: 6,
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
          color: "var(--text-muted)",
          fontSize: 12,
        }}
      >
        Online
      </span>
    </div>
  </div>

  <style>
    {`
      .character-card:hover {
        transform: translateY(-2px);
        border-color: var(--primary) !important;
        box-shadow:
          0 0 30px rgba(139,124,255,.22),
          0 10px 30px rgba(0,0,0,.25);
      }

      .character-card:hover img {
        box-shadow:
          0 0 20px rgba(139,124,255,.35),
          0 0 40px rgba(95,214,255,.15);
      }
    `}
  </style>
</button>


);
}
