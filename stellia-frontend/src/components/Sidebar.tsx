import CharacterCard from "./CharacterCard";
import type { Character } from "../App";

interface SidebarProps {
  characters: Character[];
  selectedCharacterId: string;
  coins: number;
  username: string;
  level: number;
}

export default function Sidebar({
  characters,
  selectedCharacterId,
  coins,
  username,
  level,
}: SidebarProps) {
  return (
    <aside
      className="sidebar"
      style={{
        position: "relative",
        zIndex: 2,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        padding: "24px",
        background: "linear-gradient(180deg, rgba(17,21,40,.9), rgba(9,11,20,.95))",
      }}
    >
      {/* Logo */}
      <div style={{ marginBottom: 24 }}>
        <div
          style={{
            fontSize: 36,
            fontWeight: 800,
            letterSpacing: "-0.04em",
            background: "var(--gradient-cosmic)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          Stellia
        </div>
        <div style={{ marginTop: 4, color: "var(--text-muted)", fontSize: 13 }}>
          Meet Fate. Beyond Worlds.
        </div>
      </div>

      {/* Coin Card */}
      <div
        className="glass-card glow-hover"
        style={{
          borderRadius: 24,
          padding: 18,
          marginBottom: 24,
          background: "linear-gradient(135deg, rgba(246,198,91,.18), rgba(246,198,91,.04))",
          border: "1px solid rgba(246,198,91,.25)",
        }}
      >
        <div style={{ color: "var(--text-muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: ".12em" }}>
          Lucky Coin Balance
        </div>
        <div style={{ marginTop: 10, fontSize: 28, fontWeight: 700, color: "var(--gold)", textShadow: "0 0 20px rgba(246,198,91,.35)" }}>
          ✦ {coins.toLocaleString()}
        </div>
      </div>

      {/* Characters */}
      <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 12, letterSpacing: ".12em", textTransform: "uppercase" }}>
        Celestial Companions
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, overflowY: "auto", flex: 1, paddingRight: 4 }}>
        {characters.map((character) => (
          <CharacterCard
            key={character.id}
            character={character}
            active={selectedCharacterId === character.id}
          />
        ))}
      </div>

      {/* User */}
      <div
        className="glass-card"
        style={{ marginTop: 18, borderRadius: 22, padding: 16, display: "flex", alignItems: "center", gap: 12 }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            background: "var(--gradient-cosmic)",
            display: "grid",
            placeItems: "center",
            fontWeight: 700,
            boxShadow: "var(--shadow-glow-primary)",
          }}
        >
          A
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600 }}>{username}</div>
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Level {level}</div>
        </div>
        <button
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "var(--bg-elevated)",
            color: "var(--text-secondary)",
            transition: "all .2s ease",
          }}
        >
          ⚙
        </button>
      </div>
    </aside>
  );
}