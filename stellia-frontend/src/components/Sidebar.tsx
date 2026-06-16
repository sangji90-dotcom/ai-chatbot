import CharacterCard from "./CharacterCard";
import type { Character } from "../App";

interface SidebarProps {
  characters: Character[];
  selectedCharacterId: string;
  coins: number;
  username: string;
  level: number;
  onSelectCharacter: (char: Character) => void;
  onLogout: () => void;
  onCreateCharacter: () => void;
  onMyPage: () => void;
  onSearch: () => void;
}

export default function Sidebar({
  characters,
  selectedCharacterId,
  coins,
  username,
  level,
  onSelectCharacter,
  onLogout,
  onCreateCharacter,
  onMyPage,
  onSearch,
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
      {/* 로고 */}
      <div style={{ marginBottom: 20 }}>
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

      {/* 검색창 */}
      <div
        onClick={onSearch}
        className="glass-card"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "12px 16px",
          borderRadius: 16,
          marginBottom: 20,
          cursor: "pointer",
          transition: "all .2s ease",
        }}
      >
        <span style={{ color: "var(--text-muted)", fontSize: 16 }}>🔍</span>
        <span style={{ color: "var(--text-muted)", fontSize: 14 }}>캐릭터 검색...</span>
      </div>

      {/* 럭키 코인 */}
      <div
        className="glass-card"
        style={{
          borderRadius: 24,
          padding: 18,
          marginBottom: 20,
          background: "linear-gradient(135deg, rgba(246,198,91,.18), rgba(246,198,91,.04))",
          border: "1px solid rgba(246,198,91,.25)",
        }}
      >
        <div style={{ color: "var(--text-muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: ".12em" }}>
          럭키 코인 잔액
        </div>
        <div style={{ marginTop: 10, fontSize: 28, fontWeight: 700, color: "var(--gold)", textShadow: "0 0 20px rgba(246,198,91,.35)" }}>
          ✦ {coins.toLocaleString()}
        </div>
      </div>

      {/* 캐릭터 헤더 + 만들기 버튼 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase" }}>
          캐릭터
        </div>
        <button
          onClick={onCreateCharacter}
          style={{
            padding: "6px 12px",
            borderRadius: 10,
            border: "1px solid rgba(139,124,255,.4)",
            background: "rgba(139,124,255,.12)",
            color: "var(--primary)",
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            transition: "all .2s ease",
          }}
        >
          + 만들기
        </button>
      </div>

      {/* 캐릭터 목록 */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, overflowY: "auto", flex: 1, paddingRight: 4 }}>
        {characters.map((character) => (
          <CharacterCard
            key={character.id}
            character={character}
            active={selectedCharacterId === character.id}
            onClick={() => onSelectCharacter(character)}
          />
        ))}
      </div>

      {/* 유저 */}
      <div
        className="glass-card"
        onClick={onMyPage}
        style={{
          marginTop: 18, borderRadius: 22, padding: 16,
          display: "flex", alignItems: "center", gap: 12,
          cursor: "pointer",
        }}
      >
        <div
          style={{
            width: 48, height: 48, borderRadius: "50%",
            background: "var(--gradient-cosmic)",
            display: "grid", placeItems: "center",
            fontWeight: 700, boxShadow: "var(--shadow-glow-primary)",
          }}
        >
          {username[0]?.toUpperCase() ?? "U"}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600 }}>{username}</div>
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Lv.{level}</div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onLogout(); }}
          style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "var(--bg-elevated)",
            color: "var(--text-secondary)",
            transition: "all .2s ease",
          }}
          title="로그아웃"
        >
          ⚙
        </button>
      </div>
    </aside>
  );
}