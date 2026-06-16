import { useState } from "react";
import type { Character } from "../App";
import CreatorProfileModal from "./CreatorProfileModal";

interface ChatHeaderProps {
  character: Character;
  apiUrl: string;
  token: string;
  onSelectCharacter?: (char: Character) => void;
  onBack?: () => void;
}

export default function ChatHeader({ character, apiUrl, token, onSelectCharacter, onBack }: ChatHeaderProps) {
  const [showCreator, setShowCreator] = useState(false);

  return (
    <>
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
          background: "linear-gradient(to bottom, rgba(17,21,40,.85), rgba(17,21,40,.55))",
        }}
      >
        {/* 왼쪽 */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* 뒤로가기 */}
          {onBack && (
            <button
              onClick={onBack}
              style={{
                width: 40, height: 40, borderRadius: 12,
                border: "1px solid var(--border-default)",
                background: "rgba(24,29,54,.75)",
                color: "var(--text-secondary)",
                fontSize: 18, cursor: "pointer",
              }}
            >
              ←
            </button>
          )}

          {/* 아바타 */}
          <div style={{ position: "relative" }}>
            {character.avatar ? (
              <img
                src={character.avatar}
                alt={character.name}
                style={{
                  width: 56, height: 56, borderRadius: "50%",
                  objectFit: "cover",
                  border: "2px solid var(--primary)",
                  boxShadow: "0 0 20px rgba(139,124,255,.35)",
                }}
              />
            ) : (
              <div
                style={{
                  width: 56, height: 56, borderRadius: "50%",
                  background: "var(--gradient-cosmic)",
                  display: "grid", placeItems: "center",
                  fontWeight: 700, fontSize: 22,
                  border: "2px solid var(--primary)",
                  boxShadow: "0 0 20px rgba(139,124,255,.35)",
                }}
              >
                {character.name[0]}
              </div>
            )}
            {character.online && (
              <span
                style={{
                  position: "absolute", right: 2, bottom: 2,
                  width: 12, height: 12, borderRadius: "50%",
                  background: "#41D980",
                  border: "2px solid var(--bg-base)",
                  boxShadow: "0 0 10px #41D980",
                }}
              />
            )}
          </div>

          {/* 이름 */}
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
              {character.name}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#41D980" }} />
              <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                {character.title || "온라인"}
              </span>
            </div>
          </div>
        </div>

        {/* 오른쪽 */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* 창작자 프로필 버튼 */}
          <ActionButton icon="👤" onClick={() => setShowCreator(true)} title="창작자 프로필" />
          <ActionButton icon="♡" title="좋아요" />
          <ActionButton icon="⋯" title="더보기" />
        </div>
      </header>

      {/* 창작자 프로필 모달 */}
      {showCreator && character.user_id && (
        <CreatorProfileModal
          apiUrl={apiUrl}
          token={token}
          userId={character.user_id}
          onClose={() => setShowCreator(false)}
          onSelectCharacter={onSelectCharacter}
        />
      )}
    </>
  );
}

function ActionButton({
  icon,
  onClick,
  title,
}: {
  icon: string;
  onClick?: () => void;
  title?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      style={{
        width: 44, height: 44, borderRadius: 14,
        border: "1px solid var(--border-default)",
        background: "rgba(24,29,54,.75)",
        color: "var(--text-secondary)",
        fontSize: 18, transition: "all .2s ease",
        backdropFilter: "blur(12px)", cursor: "pointer",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = "var(--primary)";
        e.currentTarget.style.color = "var(--text-primary)";
        e.currentTarget.style.boxShadow = "0 0 20px rgba(139,124,255,.25)";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = "var(--border-default)";
        e.currentTarget.style.color = "var(--text-secondary)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {icon}
    </button>
  );
}