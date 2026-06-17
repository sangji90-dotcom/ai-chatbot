import { useState } from "react";
import type { Character } from "../App";
import CreatorProfileModal from "./CreatorProfileModal";

interface ChatHeaderProps {
  character: Character;
  apiUrl: string;
  token: string;
  sessionId: string;
  coins?: number;
  showPanel?: boolean;
  onSelectCharacter?: (char: Character) => void;
  onBack?: () => void;
  onShowProfile?: () => void;
  onShowRoomModal?: () => void;
  onTogglePanel?: () => void;
}

export default function ChatHeader({
  character, apiUrl, token, coins,
  showPanel, onSelectCharacter, onBack,
  onShowProfile, onShowRoomModal, onTogglePanel
}: ChatHeaderProps) {
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

          {/* 아바타 + 이름 클릭 시 프로필 모달 */}
          <div
            onClick={onShowProfile}
            style={{ display: "flex", alignItems: "center", gap: 16, cursor: "pointer" }}
          >
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
        </div>

        {/* 오른쪽 */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* 코인 */}
          {coins !== undefined && (
            <div style={{ color: "var(--gold)", fontWeight: 600, fontSize: 14 }}>
              ✦ {coins.toLocaleString()}
            </div>
          )}

          {/* 창작자 프로필 */}
          <ActionButton icon="👤" onClick={() => setShowCreator(true)} title="창작자 프로필" />

          {/* 캐릭터 이미지 패널 토글 */}
          <ActionButton
            icon="🖼"
            onClick={onTogglePanel}
            title="캐릭터 이미지"
            active={showPanel}
          />

          {/* 채팅방 관리 */}
          <ActionButton icon="⋯" onClick={onShowRoomModal} title="채팅방 관리" />
        </div>
      </header>

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
  icon, onClick, title, active,
}: {
  icon: string;
  onClick?: () => void;
  title?: string;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      style={{
        width: 44, height: 44, borderRadius: 14,
        border: active ? "1px solid var(--primary)" : "1px solid var(--border-default)",
        background: active ? "rgba(139,124,255,.15)" : "rgba(24,29,54,.75)",
        color: active ? "var(--primary)" : "var(--text-secondary)",
        fontSize: 18, transition: "all .2s ease",
        backdropFilter: "blur(12px)", cursor: "pointer",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = "var(--primary)";
        e.currentTarget.style.color = "var(--text-primary)";
        e.currentTarget.style.boxShadow = "0 0 20px rgba(139,124,255,.25)";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = active ? "var(--primary)" : "var(--border-default)";
        e.currentTarget.style.color = active ? "var(--primary)" : "var(--text-secondary)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {icon}
    </button>
  );
}