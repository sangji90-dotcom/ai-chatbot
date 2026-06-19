import axios from "axios";
import { useState, useEffect } from "react";
import type { Character } from "../App";

interface CharacterProfileModalProps {
  character: Character;
  apiUrl: string;
  token: string;
  onClose: () => void;
  onGoParty?: (roomCode: string) => void;
}

export default function CharacterProfileModal({ character, apiUrl, token, onClose, onGoParty }: CharacterProfileModalProps) {
  const [liked, setLiked] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [partyLoading, setPartyLoading] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!token) return;
    axios.get(`${apiUrl}/likes/bookmarks/${character.id}/status`, { headers })
      .then(res => setBookmarked(res.data.bookmarked))
      .catch(console.error);
  }, [character.id]);

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

  const handleBookmark = async () => {
    try {
      if (bookmarked) {
        await axios.delete(`${apiUrl}/likes/bookmarks/${character.id}`, { headers });
      } else {
        await axios.post(`${apiUrl}/likes/bookmarks/${character.id}`, {}, { headers });
      }
      setBookmarked(!bookmarked);
    } catch {
      console.error("북마크 실패");
    }
  };

  const handlePartyChat = async () => {
    setPartyLoading(true);
    try {
      const res = await axios.post(`${apiUrl}/party/rooms`,
        { story_id: 1, max_members: 4 }, { headers });
      onClose();
      onGoParty?.(res.data.code);
    } catch {
      alert("파티방 생성에 실패했어요.");
    } finally {
      setPartyLoading(false);
    }
  };

  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,.6)", backdropFilter: "blur(4px)" }} />

      <div style={{
        position: "fixed", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)", zIndex: 51,
        width: 420, maxWidth: "90vw", maxHeight: "85vh",
        borderRadius: 28, overflow: "hidden",
        border: "1px solid var(--border-default)",
        background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
        boxShadow: "0 0 60px rgba(0,0,0,.5), 0 0 30px rgba(139,124,255,.1)",
        display: "flex", flexDirection: "column",
      }}>
        {/* 캐릭터 이미지 */}
        <div style={{ position: "relative", height: 220, flexShrink: 0 }}>
          {character.avatar ? (
            <img src={character.avatar} alt={character.name}
              style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div style={{
              width: "100%", height: "100%",
              background: "var(--gradient-cosmic)",
              display: "grid", placeItems: "center",
              fontSize: 80, fontWeight: 700,
            }}>{character.name[0]}</div>
          )}
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.95), transparent 50%)" }} />
          <button onClick={onClose} style={{
            position: "absolute", top: 16, right: 16,
            width: 36, height: 36, borderRadius: 10,
            border: "1px solid rgba(255,255,255,.2)",
            background: "rgba(0,0,0,.4)",
            color: "#fff", fontSize: 18, cursor: "pointer",
            backdropFilter: "blur(8px)",
          }}>×</button>
          <div style={{ position: "absolute", bottom: 16, left: 20, right: 20 }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#fff" }}>{character.name}</div>
            {character.title && (
              <div style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 4 }}>{character.title}</div>
            )}
          </div>
        </div>

        {/* 내용 */}
        <div style={{ overflowY: "auto", flex: 1, padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          {character.tags.length > 0 && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {character.tags.map(tag => (
                <span key={tag} style={{
                  padding: "5px 12px", borderRadius: 999,
                  background: "rgba(139,124,255,.12)",
                  border: "1px solid rgba(139,124,255,.2)",
                  color: "var(--primary)", fontSize: 12, fontWeight: 600,
                }}>#{tag}</span>
              ))}
            </div>
          )}

          {character.description && (
            <div style={{
              padding: 16, borderRadius: 16,
              background: "rgba(255,255,255,.03)",
              border: "1px solid var(--border-subtle)",
            }}>
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 8, letterSpacing: ".1em" }}>소개</div>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.8, fontSize: 14, margin: 0 }}>
                {character.description}
              </p>
            </div>
          )}

          {/* 액션 버튼 */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button onClick={handleLike} style={{
              flex: 1, padding: "12px", borderRadius: 14,
              border: liked ? "1px solid rgba(255,107,138,.4)" : "1px solid var(--border-default)",
              background: liked ? "rgba(255,107,138,.12)" : "rgba(255,255,255,.04)",
              color: liked ? "#ff6b8a" : "var(--text-muted)",
              fontWeight: 600, fontSize: 14, cursor: "pointer", transition: "all .2s ease",
            }}>{liked ? "♥" : "♡"} 좋아요</button>

            <button onClick={handleBookmark} style={{
              flex: 1, padding: "12px", borderRadius: 14,
              border: bookmarked ? "1px solid rgba(255,200,80,.4)" : "1px solid var(--border-default)",
              background: bookmarked ? "rgba(255,200,80,.12)" : "rgba(255,255,255,.04)",
              color: bookmarked ? "#ffc850" : "var(--text-muted)",
              fontWeight: 600, fontSize: 14, cursor: "pointer", transition: "all .2s ease",
            }}>{bookmarked ? "★" : "☆"} 북마크</button>

            <button onClick={() => {
              window.location.hash = `#/characters/${character.id}`;
              navigator.clipboard.writeText(window.location.href);
            }} style={{
              flex: 1, padding: "12px", borderRadius: 14,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)",
              fontWeight: 600, fontSize: 14, cursor: "pointer",
            }}>⤴ 공유</button>
          </div>

          {/* 파티챗 버튼 */}
          {character.party_enabled && token && (
            <button onClick={handlePartyChat} disabled={partyLoading} style={{
              width: "100%", padding: "12px", borderRadius: 14,
              border: "1px solid rgba(139,124,255,.4)",
              background: "rgba(139,124,255,.12)",
              color: "var(--primary)",
              fontWeight: 600, fontSize: 14, cursor: "pointer",
              opacity: partyLoading ? 0.6 : 1,
            }}>⚔ 파티챗 방 만들기</button>
          )}
        </div>
      </div>
    </>
  );
}