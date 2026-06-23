import { useState, useEffect } from "react";
import axios from "axios";
import type { Character } from "../App";

interface CreatorPageProps {
  apiUrl: string;
  token: string;
  userId: number;
  onBack: () => void;
  onSelectCharacter: (char: Character) => void;
}

const formatChar = (c: any): Character => ({
  id: c.id, name: c.name,
  title: c.description || "",
  avatar: c.image_url || "",
  description: c.description || "",
  online: true, tags: c.tags || [],
  user_id: c.user_id,
  first_message: c.first_message || "",
  party_enabled: c.party_enabled || false,
  like_count: c.like_count ?? 0,
  chat_count: c.chat_count ?? 0,
  view_count: c.view_count ?? 0,
});

export default function CreatorPage({ apiUrl, token, userId, onBack, onSelectCharacter }: CreatorPageProps) {
  const [creator, setCreator] = useState<any>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followerCount, setFollowerCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [followLoading, setFollowLoading] = useState(false);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    Promise.all([
      axios.get(`${apiUrl}/users/${userId}`, { headers }),
      axios.get(`${apiUrl}/characters/user/${userId}`, { headers }),
    ]).then(([userRes, charRes]) => {
      setCreator(userRes.data);
      setIsFollowing(userRes.data.is_following ?? false);
      setFollowerCount(userRes.data.follower_count ?? 0);
      setCharacters(charRes.data.map(formatChar));
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, [userId]);

  const handleFollow = async () => {
    if (!token) return;
    setFollowLoading(true);
    try {
      if (isFollowing) {
        await axios.delete(`${apiUrl}/follows/${userId}`, { headers });
        setIsFollowing(false);
        setFollowerCount(prev => prev - 1);
      } else {
        await axios.post(`${apiUrl}/follows/${userId}`, {}, { headers });
        setIsFollowing(true);
        setFollowerCount(prev => prev + 1);
      }
    } catch {
      console.error("팔로우 실패");
    } finally {
      setFollowLoading(false);
    }
  };

  if (loading) return (
    <div style={{ position: "relative", zIndex: 2, height: "100vh", display: "grid", placeItems: "center", color: "var(--text-muted)" }}>
      불러오는 중...
    </div>
  );

  if (!creator) return (
    <div style={{ position: "relative", zIndex: 2, height: "100vh", display: "grid", placeItems: "center", color: "var(--text-muted)" }}>
      유저를 찾을 수 없어요.
    </div>
  );

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh" }}>

      {/* 네비바 */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 10,
        display: "flex", alignItems: "center", gap: 16,
        padding: "16px 32px",
        background: "rgba(9,11,20,.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 22, cursor: "pointer" }}>←</button>
        <span style={{ fontWeight: 700, fontSize: 18 }}>창작자 프로필</span>
      </nav>

      <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 24px" }}>

        {/* 프로필 헤더 */}
        <div style={{
          borderRadius: 24, padding: 28,
          border: "1px solid var(--border-default)",
          background: "rgba(17,21,40,.7)",
          backdropFilter: "blur(20px)",
          marginBottom: 28,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 20 }}>
            {/* 아바타 */}
            <div style={{
              width: 80, height: 80, borderRadius: "50%",
              background: creator.profile_image_url ? "none" : "var(--gradient-cosmic)",
              display: "grid", placeItems: "center",
              fontWeight: 700, fontSize: 32,
              overflow: "hidden", flexShrink: 0,
              boxShadow: "var(--shadow-glow-primary)",
            }}>
              {creator.profile_image_url
                ? <img src={creator.profile_image_url} alt={creator.username}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                : creator.username?.[0]?.toUpperCase()}
            </div>

            {/* 이름 + 칭호 */}
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                {creator.equipped_prefix && (
                  <span style={{ color: "var(--primary)", fontSize: 13 }}>[{creator.equipped_prefix}]</span>
                )}
                <span style={{ fontWeight: 700, fontSize: 22 }}>{creator.username}</span>
                {creator.equipped_suffix && (
                  <span style={{ color: "var(--primary)", fontSize: 13 }}>[{creator.equipped_suffix}]</span>
                )}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 6 }}>
                가입일: {new Date(creator.created_at).toLocaleDateString("ko-KR")}
              </div>
            </div>

            {/* 팔로우 버튼 */}
            {token && (
              <button onClick={handleFollow} disabled={followLoading} style={{
                padding: "10px 24px", borderRadius: 14,
                border: isFollowing ? "1px solid var(--border-default)" : "none",
                background: isFollowing ? "rgba(255,255,255,.06)" : "var(--gradient-cosmic)",
                color: isFollowing ? "var(--text-muted)" : "#fff",
                fontWeight: 700, fontSize: 14, cursor: "pointer",
                transition: "all .2s ease",
                opacity: followLoading ? 0.7 : 1,
              }}>
                {isFollowing ? "팔로잉" : "+ 팔로우"}
              </button>
            )}
          </div>

          {/* 통계 */}
          <div style={{ display: "flex", gap: 24 }}>
            {[
              { label: "캐릭터", value: characters.length },
              { label: "팔로워", value: followerCount },
              { label: "총 대화수", value: characters.reduce((acc, c) => acc + (c.chat_count ?? 0), 0) },
            ].map(stat => (
              <div key={stat.label} style={{ textAlign: "center" }}>
                <div style={{ fontWeight: 700, fontSize: 20, color: "var(--text-primary)" }}>
                  {stat.value.toLocaleString()}
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2 }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 캐릭터 목록 */}
        <div style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
            ✦ 만든 캐릭터 {characters.length > 0 && `(${characters.length})`}
          </h2>
          {characters.length === 0 ? (
            <div style={{
              borderRadius: 20, padding: 40, textAlign: "center",
              border: "1px solid var(--border-default)",
              background: "rgba(17,21,40,.7)",
              color: "var(--text-muted)",
            }}>아직 만든 캐릭터가 없어요.</div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
              {characters.map(char => (
                <div key={char.id} onClick={() => onSelectCharacter(char)} style={{
                  borderRadius: 20, overflow: "hidden", cursor: "pointer",
                  border: "1px solid var(--border-default)",
                  background: "rgba(17,21,40,.7)",
                  transition: "all .2s ease",
                }}>
                  <div style={{ position: "relative", height: 180, overflow: "hidden" }}>
                    {char.avatar ? (
                      <img src={char.avatar} alt={char.name}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    ) : (
                      <div style={{
                        width: "100%", height: "100%",
                        background: "var(--gradient-cosmic)",
                        display: "grid", placeItems: "center",
                        fontSize: 56, fontWeight: 700,
                      }}>{char.name[0]}</div>
                    )}
                    <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.9), transparent 50%)" }} />
                  </div>
                  <div style={{ padding: "12px 14px" }}>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{char.name}</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {char.description}
                    </div>
                    <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
                      <span style={{ color: "#ff6b8a", fontSize: 11 }}>♥ {char.like_count?.toLocaleString()}</span>
                      <span style={{ color: "#5fd6ff", fontSize: 11 }}>💬 {char.chat_count?.toLocaleString()}</span>
                      <span style={{ color: "#ffc850", fontSize: 11 }}>👁 {char.view_count?.toLocaleString()}</span>
                    </div>
                    {char.tags.length > 0 && (
                      <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                        {char.tags.slice(0, 2).map(tag => (
                          <span key={tag} style={{
                            padding: "2px 7px", borderRadius: 999, fontSize: 10,
                            background: "rgba(139,124,255,.12)",
                            border: "1px solid rgba(139,124,255,.18)",
                            color: "var(--primary)",
                          }}>#{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}