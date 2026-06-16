// src/components/ProfilePanel.tsx

import type { Character } from "../App";

interface ProfilePanelProps {
character: Character;
}

export default function ProfilePanel({
character,
}: ProfilePanelProps) {
return (
<aside
className="profile-panel"
style={{
position: "relative",
zIndex: 2,
height: "100vh",
padding: 24,
overflowY: "auto",
background:
"linear-gradient(180deg, rgba(17,21,40,.92), rgba(9,11,20,.98))",
}}
>
{/* Hero Card */}
<div
className="glass-card"
style={{
borderRadius: 28,
overflow: "hidden",
marginBottom: 20,
}}
>
<div
style={{
position: "relative",
height: 180,
overflow: "hidden",
}}
>
<img
src={character.avatar}
alt={character.name}
style={{
width: "100%",
height: "100%",
objectFit: "cover",
}}
/>


      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(to top, rgba(9,11,20,.95), transparent)",
        }}
      />

      <div
        style={{
          position: "absolute",
          bottom: 18,
          left: 18,
          right: 18,
        }}
      >
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: "#fff",
          }}
        >
          {character.name}
        </div>

        <div
          style={{
            marginTop: 4,
            color: "var(--text-secondary)",
            fontSize: 14,
          }}
        >
          {character.title}
        </div>
      </div>
    </div>

    <div
      style={{
        padding: 20,
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        {character.tags.map((tag) => (
          <span
            key={tag}
            style={{
              padding: "7px 12px",
              borderRadius: 999,
              background:
                "rgba(139,124,255,.12)",
              border:
                "1px solid rgba(139,124,255,.18)",
              color: "var(--primary)",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  </div>

  {/* Description */}
  <div
    className="glass-card"
    style={{
      borderRadius: 24,
      padding: 20,
      marginBottom: 20,
    }}
  >
    <div className="panel-title">
      About
    </div>

    <p
      style={{
        margin: "14px 0 0",
        color: "var(--text-secondary)",
        lineHeight: 1.8,
        fontSize: 14,
      }}
    >
      {character.description}
    </p>
  </div>

  {/* Stats */}
  <div
    className="glass-card"
    style={{
      borderRadius: 24,
      padding: 20,
      marginBottom: 20,
    }}
  >
    <div className="panel-title">
      Celestial Stats
    </div>

    <div
      style={{
        marginTop: 18,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 14,
      }}
    >
      <StatCard
        label="Affinity"
        value="98%"
      />
      <StatCard
        label="Wisdom"
        value="SS"
      />
      <StatCard
        label="Charm"
        value="95"
      />
      <StatCard
        label="Mystique"
        value="∞"
      />
    </div>
  </div>

  {/* Actions */}
  <div
    className="glass-card"
    style={{
      borderRadius: 24,
      padding: 20,
      marginBottom: 20,
    }}
  >
    <div className="panel-title">
      Actions
    </div>

    <div
      style={{
        display: "grid",
        gap: 12,
        marginTop: 18,
      }}
    >
      <ActionButton>
        ♡ Add to Favorites
      </ActionButton>

      <ActionButton>
        ✦ Send Gift
      </ActionButton>

      <ActionButton>
        ⤴ Share Character
      </ActionButton>
    </div>
  </div>

  {/* Lucky Coin */}
  <div
    style={{
      position: "relative",
      overflow: "hidden",
      borderRadius: 24,
      padding: 22,
      background:
        "linear-gradient(135deg, rgba(246,198,91,.18), rgba(246,198,91,.05))",
      border:
        "1px solid rgba(246,198,91,.25)",
      boxShadow:
        "0 0 35px rgba(246,198,91,.12)",
    }}
  >
    <div
      style={{
        position: "absolute",
        top: -50,
        right: -50,
        width: 120,
        height: 120,
        borderRadius: "50%",
        background:
          "rgba(246,198,91,.15)",
        filter: "blur(40px)",
      }}
    />

    <div
      style={{
        position: "relative",
      }}
    >
      <div
        style={{
          color: "var(--gold)",
          fontSize: 13,
          letterSpacing: ".12em",
          textTransform: "uppercase",
        }}
      >
        Lucky Coin Bonus
      </div>

      <div
        style={{
          marginTop: 10,
          fontSize: 32,
          fontWeight: 800,
          color: "var(--gold)",
          textShadow:
            "0 0 20px rgba(246,198,91,.35)",
        }}
      >
        +25 ✦
      </div>

      <div
        style={{
          marginTop: 8,
          color: "var(--text-secondary)",
          lineHeight: 1.7,
          fontSize: 14,
        }}
      >
        Increase affinity and unlock
        special story routes.
      </div>
    </div>
  </div>
</aside>


);
}

function StatCard({
label,
value,
}: {
label: string;
value: string;
}) {
return (
<div
style={{
borderRadius: 18,
padding: 16,
background:
"rgba(255,255,255,.02)",
border:
"1px solid var(--border-default)",
}}
>
<div
style={{
color: "var(--text-muted)",
fontSize: 12,
}}
>
{label} </div>


  <div
    style={{
      marginTop: 8,
      fontWeight: 700,
      fontSize: 20,
      color: "var(--text-primary)",
    }}
  >
    {value}
  </div>
</div>


);
}

function ActionButton({
children,
}: {
children: React.ReactNode;
}) {
return (
<button
style={{
height: 48,
borderRadius: 16,
border:
"1px solid var(--border-default)",
background:
"rgba(255,255,255,.02)",
color: "var(--text-primary)",
transition: "all .2s ease",
}}
>
{children} </button>
);
}
