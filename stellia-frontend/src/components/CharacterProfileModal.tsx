import axios from "axios";
import { useState } from "react";
import type { Character } from "../App";

interface CharacterProfileModalProps {
  character: Character;
  apiUrl: string;
  token: string;
  onClose: () => void;
}

export default function CharacterProfileModal({ character, apiUrl, token, onClose }: CharacterProfileModalProps) {
  const [liked, setLiked] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const handleLike = async () => {
    try {
      if (liked) {
        await axios.delete(`${apiUrl}/likes/${character.id}`, { headers });
        setLiked(false);
      } else {
        await axios.post(`${apiUrl}/likes/${character.id}`, {}, { headers });
        setLiked(true);
      }
    } catch {
      console.error("좋아요 실패");
    }
  };

  return (
    <>
      {/* 오버레이 */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.6)",
          backdropFilter: "blur(4px)",
        }}
      />

      {/* 모달 */}
      <div
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 420, maxWidth: "90vw",
          maxHeight: "85vh",
          borderRadius: 28,
          overflow: "hidden",
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(0,0,0,.5), 0 0 30px rgba(139,124,255,.1)",
          display: "flex", flexDirection: "column",
        }}
      >
        {/* 캐릭터 이미지 */}
        <div style={{ position: "relative", height: 220, flexShrink: 0 }}>
          {character.avatar ? (
            <img
              src={character.avatar}
              alt={character.name}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          ) : (
            <div
              style={{
                width: "100%", height: "100%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontSize: 80, fontWeight: 700,
              }}
            >
              {character.name[0]}
            </div>
          )}
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.95), transparent 50%)" }} />

          {/* 닫기 버튼 */}
          <button
            onClick={onClose}
            style={{
              position: "absolute", top: 16, right: 16,
              width: 36, height: 36, borderRadius: 10,
              border: "1px solid rgba(255,255,255,.2)",
              background: "rgba(0,0,0,.4)",
              color: "#fff", fontSize: 18, cursor: "pointer",
              backdropFilter: "blur(8px)",
            }}
          >
            ×
          </button>

          {/* 이름 */}
          <div style={{ position: "absolute", bottom: 16, left: 20, right: 20 }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#fff" }}>{character.name}</div>
            {character.title && (
              <div style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 4 }}>{character.title}</div>
            )}
          </div>
        </div>

        {/* 내용 */}
        <div style={{ overflowY: "auto", flex: 1, padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          {/* 태그 */}
          {character.tags.length > 0 && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {character.tags.map(tag => (
                <span
                  key={tag}
                  style={{
                    padding: "5px 12px", borderRadius: 999,
                    background: "rgba(139,124,255,.12)",
                    border: "1px solid rgba(139,124,255,.2)",
                    color: "var(--primary)", fontSize: 12, fontWeight: 600,
                  }}
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* 소개 */}
          {character.description && (
            <div
              style={{
                padding: 16, borderRadius: 16,
                background: "rgba(255,255,255,.03)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 8, letterSpacing: ".1em" }}>소개</div>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.8, fontSize: 14, margin: 0 }}>
                {character.description}
              </p>
            </div>
          )}

          {/* 액션 버튼 */}
          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={handleLike}
              style={{
                flex: 1, padding: "12px", borderRadius: 14,
                border: liked ? "1px solid rgba(255,107,138,.4)" : "1px solid var(--border-default)",
                background: liked ? "rgba(255,107,138,.12)" : "rgba(255,255,255,.04)",
                color: liked ? "#ff6b8a" : "var(--text-muted)",
                fontWeight: 600, fontSize: 14, cursor: "pointer",
                transition: "all .2s ease",
              }}
            >
              {liked ? "♥" : "♡"} 좋아요
            </button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
              }}
              style={{
                flex: 1, padding: "12px", borderRadius: 14,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.04)",
                color: "var(--text-muted)",
                fontWeight: 600, fontSize: 14, cursor: "pointer",
              }}
            >
              ⤴ 공유
            </button>
          </div>
        </div>
      </div>
    </>
  );
}