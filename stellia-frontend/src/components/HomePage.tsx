import { useState, useEffect } from "react";
import axios from "axios";
import type { Character, User } from "../App";
import CoinModal from "./CoinModal";
import NotificationModal from "./NotificationModal";

interface HomePageProps {
  apiUrl: string;
  token: string;
  user: User | null;
  onSelectCharacter: (char: Character) => void;
  onLogout: () => void;
  onGoParty: () => void;
  onCreateCharacter: () => void;
  onGoEvents: () => void;
  onGoMyPage: () => void;
  onGoRanking: () => void
}

const CATEGORIES = ["전체", "로맨스", "판타지", "액션", "일상", "공포", "SF", "BL", "GL", "기타"];

export default function HomePage({ apiUrl, token, user, onSelectCharacter, onLogout, onGoParty, onCreateCharacter, onGoEvents, onGoMyPage, onGoRanking }: HomePageProps) {
  const [activeCategory, setActiveCategory] = useState("전체");
  const [characters, setCharacters] = useState<Character[]>([]);
  const [newCharacters, setNewCharacters] = useState<Character[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [showCoinModal, setShowCoinModal] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [coins, setCoins] = useState<number>(user?.token_balance ?? 0);
  const [unreadCount, setUnreadCount] = useState(0);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const formatChar = (c: any): Character => ({
    id: c.id, name: c.name,
    title: c.description || "",
    avatar: c.image_url || "",
    description: c.description || "",
    online: true, tags: c.tags || [],
    user_id: c.user_id,
    first_message: c.first_message || "",
  });

  useEffect(() => {
    setLoading(true);
    Promise.all([
      axios.get(`${apiUrl}/characters/ranking?limit=20`, { headers }),
      axios.get(`${apiUrl}/characters/new?limit=10`, { headers }),
    ]).then(([rankRes, newRes]) => {
      setCharacters(rankRes.data.map(formatChar));
      setNewCharacters(newRes.data.map(formatChar));
    }).catch(console.error).finally(() => setLoading(false));

    if (token && token !== "") {
      axios.get(`${apiUrl}/notifications/unread-count`, { headers })
        .then(res => setUnreadCount(res.data.count))
        .catch(console.error);
    }
  }, []);

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    if (cat === "전체") {
      axios.get(`${apiUrl}/characters/ranking?limit=20`, { headers })
        .then(res => setCharacters(res.data.map(formatChar)));
    } else {
      axios.get(`${apiUrl}/characters?tag=${encodeURIComponent(cat)}&size=20`, { headers })
        .then(res => setCharacters(res.data.map(formatChar)));
    }
  };

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      axios.get(`${apiUrl}/characters/search?q=${encodeURIComponent(searchQuery)}`, { headers })
        .then(res => setCharacters(res.data.map(formatChar)));
    }
  };

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh", display: "flex", flexDirection: "column" }}>

      {/* 네비바 */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 10,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "16px 32px",
        background: "rgba(9,11,20,.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <div style={{
          fontSize: 28, fontWeight: 800,
          background: "var(--gradient-cosmic)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          letterSpacing: "-0.04em",
        }}>Stellia</div>

        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "10px 18px", borderRadius: 14,
          border: "1px solid var(--border-default)",
          background: "rgba(255,255,255,.04)", width: 320,
        }}>
          <span style={{ color: "var(--text-muted)" }}>🔍</span>
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
            placeholder="캐릭터 검색..."
            style={{ flex: 1, border: "none", outline: "none", background: "transparent", color: "var(--text-primary)", fontSize: 14 }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {user && (
            <button onClick={onCreateCharacter} style={{
              padding: "8px 14px", borderRadius: 10,
              border: "1px solid rgba(95,214,255,.4)",
              background: "rgba(95,214,255,.08)",
              color: "var(--secondary)", fontSize: 13, fontWeight: 600, cursor: "pointer",
            }}>✦ 캐릭터 만들기</button>
          )}

          {user && (
            <button onClick={onGoParty} style={{
              padding: "8px 14px", borderRadius: 10,
              border: "1px solid rgba(139,124,255,.4)",
              background: "rgba(139,124,255,.12)",
              color: "var(--primary)", fontSize: 13, fontWeight: 600, cursor: "pointer",
            }}>⚔ 파티챗</button>
          )}

          {user && (
            <button onClick={onGoEvents} style={{
              padding: "8px 14px", borderRadius: 10,
              border: "1px solid rgba(255,200,80,.4)",
              background: "rgba(255,200,80,.08)",
              color: "#ffc850", fontSize: 13, fontWeight: 600, cursor: "pointer",
            }}>🎁 이벤트</button>
          )}

          {user && (
            <button onClick={onGoRanking} style={{
              padding: "8px 14px", borderRadius: 10,
              border: "1px solid rgba(73,216,154,.4)",
              background: "rgba(73,216,154,.08)",
              color: "#49d89a", fontSize: 13,
              fontWeight: 600, cursor: "pointer",
            }}>🏆 랭킹</button>
          )}

          {user && (
            <div onClick={() => { setShowNotification(true); setUnreadCount(0); }}
              style={{ position: "relative", cursor: "pointer" }}>
              <span style={{ fontSize: 20 }}>🔔</span>
              {unreadCount > 0 && (
                <span style={{
                  position: "absolute", top: -6, right: -6,
                  width: 16, height: 16, borderRadius: "50%",
                  background: "var(--primary)", color: "#fff",
                  fontSize: 10, fontWeight: 700,
                  display: "grid", placeItems: "center",
                }}>{unreadCount}</span>
              )}
            </div>
          )}

          {user && (
            <div onClick={() => setShowCoinModal(true)}
              style={{ color: "var(--gold)", fontWeight: 600, fontSize: 14, cursor: "pointer" }}>
              ✦ {coins.toLocaleString()}
            </div>
          )}

          {user && (
            <div onClick={onGoMyPage} style={{
              width: 38, height: 38, borderRadius: "50%",
              background: "var(--gradient-cosmic)",
              display: "grid", placeItems: "center",
              fontWeight: 700, cursor: "pointer",
              boxShadow: "var(--shadow-glow-primary)",
              overflow: "hidden",
            }}>
              {user.profile_image_url ? (
                <img src={user.profile_image_url} alt={user.username}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : (
                user.username?.[0]?.toUpperCase()
              )}
            </div>
          )}

          {user ? (
            <button onClick={onLogout} style={{
              padding: "8px 14px", borderRadius: 10,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", fontSize: 13, cursor: "pointer",
            }}>로그아웃</button>
          ) : (
            <button onClick={onLogout} style={{
              padding: "8px 14px", borderRadius: 10,
              border: "1px solid var(--primary)",
              background: "rgba(139,124,255,.12)",
              color: "var(--primary)", fontSize: 13, fontWeight: 600, cursor: "pointer",
            }}>로그인</button>
          )}
        </div>
      </nav>

      {/* 카테고리 탭 */}
      <div style={{
        display: "flex", gap: 8, padding: "16px 32px",
        overflowX: "auto",
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(9,11,20,.6)",
      }}>
        {CATEGORIES.map(cat => (
          <button key={cat} onClick={() => handleCategoryChange(cat)} style={{
            padding: "8px 18px", borderRadius: 999,
            border: activeCategory === cat ? "none" : "1px solid var(--border-default)",
            background: activeCategory === cat ? "var(--gradient-cosmic)" : "rgba(255,255,255,.04)",
            color: activeCategory === cat ? "#fff" : "var(--text-muted)",
            fontWeight: 600, fontSize: 14, cursor: "pointer",
            whiteSpace: "nowrap", transition: "all .2s ease",
          }}>{cat}</button>
        ))}
      </div>

      {/* 메인 콘텐츠 */}
      <div style={{ flex: 1, padding: "32px", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
        {loading ? (
          <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "80px 0" }}>불러오는 중...</div>
        ) : (
          <>
            {activeCategory === "전체" && newCharacters.length > 0 && (
              <section style={{ marginBottom: 48 }}>
                <div style={{ marginBottom: 20 }}>
                  <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>✨ 신규 캐릭터</h2>
                </div>
                <div style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 8 }}>
                  {newCharacters.map(char => (
                    <CharacterCard key={char.id} character={char} onClick={() => onSelectCharacter(char)} />
                  ))}
                </div>
              </section>
            )}

            <section>
              <div style={{ marginBottom: 20 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
                  {activeCategory === "전체" ? "🔥 인기 캐릭터" : `# ${activeCategory}`}
                </h2>
              </div>
              {characters.length === 0 ? (
                <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "60px 0" }}>캐릭터가 없어요.</div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 20 }}>
                  {characters.map(char => (
                    <CharacterCard key={char.id} character={char} onClick={() => onSelectCharacter(char)} />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>

      {showCoinModal && token && (
        <CoinModal
          apiUrl={apiUrl}
          token={token}
          onClose={() => setShowCoinModal(false)}
          onCoinsUpdated={(balance) => setCoins(balance)}
        />
      )}

      {showNotification && token && (
        <NotificationModal
          apiUrl={apiUrl}
          token={token}
          onClose={() => setShowNotification(false)}
        />
      )}
    </div>
  );
}

function CharacterCard({ character, onClick }: { character: Character; onClick: () => void }) {
  return (
    <div onClick={onClick} style={{
      borderRadius: 20, overflow: "hidden",
      cursor: "pointer", transition: "all .2s ease",
      border: "1px solid var(--border-default)",
      background: "rgba(17,21,40,.7)",
      backdropFilter: "blur(16px)", minWidth: 180,
    }}>
      <div style={{ position: "relative", height: 200, overflow: "hidden" }}>
        {character.avatar ? (
          <img src={character.avatar} alt={character.name}
            style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <div style={{
            width: "100%", height: "100%",
            background: "var(--gradient-cosmic)",
            display: "grid", placeItems: "center",
            fontSize: 64, fontWeight: 700,
          }}>{character.name[0]}</div>
        )}
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.9), transparent 50%)" }} />
      </div>
      <div style={{ padding: "14px 16px" }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)" }}>{character.name}</div>
        <div style={{ marginTop: 4, color: "var(--text-muted)", fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {character.description}
        </div>
        {character.tags.length > 0 && (
          <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
            {character.tags.slice(0, 2).map(tag => (
              <span key={tag} style={{
                padding: "3px 8px", borderRadius: 999,
                background: "rgba(139,124,255,.12)",
                border: "1px solid rgba(139,124,255,.18)",
                color: "var(--primary)", fontSize: 11,
              }}>#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}