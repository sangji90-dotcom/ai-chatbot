import { useState } from "react";
import axios from "axios";
import type { Character } from "../App";
import CreatorProfileModal from "./CreatorProfileModal";

interface ChatHeaderProps {
  character: Character;
  apiUrl: string;
  token: string;
  sessionId: string;
  onSelectCharacter?: (char: Character) => void;
  onBack?: () => void;
}

export default function ChatHeader({ character, apiUrl, token, sessionId, onSelectCharacter, onBack }: ChatHeaderProps) {
  const [showCreator, setShowCreator] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleExportPdf = async () => {
    setDownloading(true);
    try {
      const res = await axios.get(
        `${apiUrl}/chat/export/${character.id}?session_id=${sessionId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: "blob",
        }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${character.name}_대화.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("PDF 내보내기에 실패했어요.");
    } finally {
      setDownloading(false);
    }
  };

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

        {/* 오른쪽 */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <ActionButton icon="👤" onClick={() => setShowCreator(true)} title="창작자 프로필" />
          <ActionButton icon="♡" title="좋아요" />
          <ActionButton
            icon={downloading ? "⏳" : "📄"}
            onClick={handleExportPdf}
            title="대화 PDF 내보내기"
          />
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
  icon, onClick, title,
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