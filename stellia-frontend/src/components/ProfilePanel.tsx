import type { Character } from "../App";

interface ProfilePanelProps {
  character: Character;
  onLike?: () => void;
}

export default function ProfilePanel({ character, onLike }: ProfilePanelProps) {
  return (
    <aside
      className="profile-panel"
      style={{
        position: "relative",
        zIndex: 2,
        height: "100vh",
        padding: 24,
        overflowY: "auto",
        background: "linear-gradient(180deg, rgba(17,21,40,.92), rgba(9,11,20,.98))",
      }}
    >
      {/* 캐릭터 프로필 */}
      <div className="glass-card" style={{ borderRadius: 28, overflow: "hidden", marginBottom: 20 }}>
        <div style={{ position: "relative", height: 200, overflow: "hidden" }}>
          {character.avatar ? (
            <img src={character.avatar} alt={character.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div
              style={{
                width: "100%", height: "100%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontSize: 72, fontWeight: 700,
              }}
            >
              {character.name[0]}
            </div>
          )}
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.95), transparent)" }} />
          <div style={{ position: "absolute", bottom: 18, left: 18, right: 18 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: "#fff" }}>{character.name}</div>
            {character.title && (
              <div style={{ marginTop: 4, color: "var(--text-secondary)", fontSize: 14 }}>{character.title}</div>
            )}
          </div>
        </div>

        {character.tags.length > 0 && (
          <div style={{ padding: "16px 20px" }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {character.tags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    padding: "6px 12px", borderRadius: 999,
                    background: "rgba(139,124,255,.12)",
                    border: "1px solid rgba(139,124,255,.18)",
                    color: "var(--primary)", fontSize: 12, fontWeight: 600,
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 소개 */}
      {character.description && (
        <div className="glass-card" style={{ borderRadius: 24, padding: 20, marginBottom: 20 }}>
          <div className="panel-title">소개</div>
          <p style={{ margin: "14px 0 0", color: "var(--text-secondary)", lineHeight: 1.8, fontSize: 14 }}>
            {character.description}
          </p>
        </div>
      )}

      {/* 액션 */}
      <div className="glass-card" style={{ borderRadius: 24, padding: 20 }}>
        <div className="panel-title">액션</div>
        <div style={{ display: "grid", gap: 12, marginTop: 18 }}>
          <button
            onClick={onLike}
            style={{
              height: 48, borderRadius: 16, width: "100%",
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.02)",
              color: "var(--text-primary)",
              cursor: "pointer", transition: "all .2s ease",
            }}
          >
            ♡ 좋아요
          </button>
          <button
            style={{
              height: 48, borderRadius: 16, width: "100%",
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.02)",
              color: "var(--text-primary)",
              cursor: "pointer", transition: "all .2s ease",
            }}
          >
            ⤴ 공유
          </button>
        </div>
      </div>
    </aside>
  );
}