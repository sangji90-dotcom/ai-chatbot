import { useState, useEffect } from "react";
import axios from "axios";
import type { Character } from "../App";

interface CreatorProfileModalProps {
  apiUrl: string;
  token: string;
  userId: number;
  onClose: () => void;
  onSelectCharacter?: (char: Character) => void;
}

export default function CreatorProfileModal({
  apiUrl,
  token,
  userId,
  onClose,
  onSelectCharacter,
}: CreatorProfileModalProps) {
  const [creator, setCreator] = useState<any>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    // 창작자 프로필
    axios.get(`${apiUrl}/users/${userId}`, { headers })
      .then(res => {
        setCreator(res.data);
        setIsFollowing(res.data.is_following);
      })
      .catch(console.error);

    // 창작자 캐릭터 목록
    axios.get(`${apiUrl}/characters/user/${userId}`, { headers })
      .then(res => {
        const chars = res.data.map((c: any) => ({
          id: c.id,
          name: c.name,
          title: c.description || "",
          avatar: c.image_url || "",
          description: c.description || "",
          online: true,
          tags: c.tags || [],
        }));
        setCharacters(chars);
      })
      .catch(console.error);
  }, [userId]);

  const handleFollow = async () => {
    setLoading(true);
    try {
      if (isFollowing) {
        await axios.delete(`${apiUrl}/follows/${userId}`, { headers });
        setIsFollowing(false);
        setCreator((prev: any) => ({ ...prev, follower_count: prev.follower_count - 1 }));
      } else {
        await axios.post(`${apiUrl}/follows/${userId}`, {}, { headers });
        setIsFollowing(true);
        setCreator((prev: any) => ({ ...prev, follower_count: prev.follower_count + 1 }));
      }
    } catch {
      alert("오류가 발생했어요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* 배경 오버레이 */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 50,
          background: "rgba(0,0,0,.6)",
          backdropFilter: "blur(4px)",
        }}
      />

      {/* 모달 */}
      <div
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 480,
          maxWidth: "90vw",
          maxHeight: "80vh",
          display: "flex",
          flexDirection: "column",
          borderRadius: 28,
          overflow: "hidden",
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(0,0,0,.5), 0 0 30px rgba(139,124,255,.1)",
        }}
      >
        {/* 헤더 */}
        <div
          style={{
            padding: "24px 24px 0",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div
              style={{
                width: 60, height: 60, borderRadius: "50%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontWeight: 700, fontSize: 24,
                boxShadow: "var(--shadow-glow-primary)",
              }}
            >
              {creator?.username?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 18 }}>{creator?.username}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
                캐릭터 {creator?.character_count ?? 0}개 · 팔로워 {creator?.follower_count ?? 0}명
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={handleFollow}
              disabled={loading}
              style={{
                padding: "10px 20px",
                borderRadius: 12,
                border: isFollowing ? "1px solid var(--border-default)" : "none",
                background: isFollowing ? "rgba(255,255,255,.04)" : "var(--gradient-cosmic)",
                color: isFollowing ? "var(--text-muted)" : "#fff",
                fontWeight: 600,
                fontSize: 14,
                cursor: "pointer",
                transition: "all .2s ease",
              }}
            >
              {loading ? "..." : isFollowing ? "팔로잉" : "팔로우"}
            </button>
            <button
              onClick={onClose}
              style={{
                width: 40, height: 40, borderRadius: 12,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.04)",
                color: "var(--text-muted)",
                fontSize: 18, cursor: "pointer",
              }}
            >
              ×
            </button>
          </div>
        </div>

        {/* 캐릭터 목록 */}
        <div style={{ padding: 24, overflowY: "auto", flex: 1 }}>
          <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 16 }}>
            만든 캐릭터
          </div>

          {characters.length === 0 ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "30px 0" }}>
              공개된 캐릭터가 없어요.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {characters.map(char => (
                <div
                  key={char.id}
                  onClick={() => {
                    if (onSelectCharacter) {
                      onSelectCharacter(char);
                      onClose();
                    }
                  }}
                  style={{
                    display: "flex", alignItems: "center", gap: 14,
                    padding: 14, borderRadius: 16,
                    border: "1px solid var(--border-default)",
                    background: "rgba(255,255,255,.02)",
                    cursor: onSelectCharacter ? "pointer" : "default",
                    transition: "all .2s ease",
                  }}
                >
                  <div
                    style={{
                      width: 44, height: 44, borderRadius: "50%",
                      background: char.avatar ? "none" : "var(--gradient-cosmic)",
                      display: "grid", placeItems: "center",
                      fontWeight: 700, fontSize: 18, flexShrink: 0,
                      overflow: "hidden",
                    }}
                  >
                    {char.avatar
                      ? <img src={char.avatar} alt={char.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                      : char.name[0]
                    }
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600 }}>{char.name}</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {char.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}