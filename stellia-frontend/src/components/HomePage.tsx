import { useState, useEffect, useRef } from "react";
import axios from "axios";
import type { Character, User } from "../App";
import CoinModal from "./CoinModal";
import NotificationModal from "./NotificationModal";
import { CharacterGridSkeleton, BannerSkeleton } from "./Skeleton";
import LazyImage from "./LazyImage";

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
  onGoRanking: () => void;
  onGoNotice: () => void;
}

const CATEGORIES = ["전체", "팔로우", "로맨스", "판타지", "액션", "일상", "공포", "SF", "BL", "GL", "기타"];

export default function HomePage({ apiUrl, token, user, onSelectCharacter, onLogout, onGoParty, onCreateCharacter, onGoEvents, onGoMyPage, onGoRanking, onGoNotice }: HomePageProps) {
  const [activeCategory, setActiveCategory] = useState("전체");
  const [characters, setCharacters] = useState<Character[]>([]);
  const [newCharacters, setNewCharacters] = useState<Character[]>([]);
  const [followFeed, setFollowFeed] = useState<Character[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [showCoinModal, setShowCoinModal] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [coins, setCoins] = useState<number>(user?.token_balance ?? 0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [banners, setBanners] = useState<any[]>([]);
  const [bannersLoading, setBannersLoading] = useState(true);
  const [bannerIndex, setBannerIndex] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const observerRef = useRef<HTMLDivElement>(null);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

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
      axios.get(`${apiUrl}/tokens/me`, { headers })
        .then(res => setCoins(res.data.token_balance))
        .catch(console.error);
      axios.get(`${apiUrl}/follows/me/new-characters`, { headers })
        .then(res => setFollowFeed(res.data.map(formatChar)))
        .catch(console.error);
    }

    axios.get(`${apiUrl}/banners`, { headers })
      .then(res => setBanners(res.data))
      .catch(console.error)
      .finally(() => setBannersLoading(false));
  }, []);

  useEffect(() => {
    if (banners.length <= 1) return;
    const timer = setInterval(() => {
      setBannerIndex(prev => (prev + 1) % banners.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [banners]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) loadMore();
      },
      { threshold: 0.5 }
    );
    if (observerRef.current) observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, activeCategory, page]);

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      let url = "";
      if (activeCategory === "전체") {
        url = `${apiUrl}/characters/ranking?limit=20&offset=${(nextPage - 1) * 20}`;
      } else if (activeCategory === "팔로우") {
        return;
      } else {
        url = `${apiUrl}/characters?tag=${encodeURIComponent(activeCategory)}&size=20&page=${nextPage}`;
      }
      const res = await axios.get(url, { headers });
      if (res.data.length === 0) {
        setHasMore(false);
      } else {
        setCharacters(prev => [...prev, ...res.data.map(formatChar)]);
        setPage(nextPage);
      }
    } catch {
      console.error("추가 로드 실패");
    } finally {
      setLoadingMore(false);
    }
  };

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    setPage(1);
    setHasMore(true);
    if (cat === "전체") {
      axios.get(`${apiUrl}/characters/ranking?limit=20`, { headers })
        .then(res => setCharacters(res.data.map(formatChar)));
    } else if (cat === "팔로우") {
      setCharacters(followFeed);
      setHasMore(false);
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

        <button onClick={() => onGoNotice()} style={{
          padding: "8px 14px", borderRadius: 10,
          border: "1px solid rgba(255,255,255,.15)",
          background: "rgba(255,255,255,.04)",
          color: "var(--text-muted)", fontSize: 13, fontWeight: 600, cursor: "pointer",
        }}>📢 공지</button>

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
              color: "#49d89a", fontSize: 13, fontWeight: 600, cursor: "pointer",
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
              ) : user.username?.[0]?.toUpperCase()}
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

      {/* 배너 */}
      {bannersLoading ? (
        <BannerSkeleton />
      ) : banners.length > 0 ? (
        <div style={{ position: "relative", height: 180, overflow: "hidden" }}>
          {banners.map((banner, i) => (
            <div key={banner.id}
              onClick={() => banner.link_url && window.open(banner.link_url, "_blank")}
              style={{
                position: "absolute", inset: 0,
                backgroundImage: `url(${banner.image_url})`,
                backgroundSize: "cover", backgroundPosition: "center",
                cursor: banner.link_url ? "pointer" : "default",
                opacity: i === bannerIndex ? 1 : 0,
                transition: "opacity 0.6s ease",
              }}
            >
              <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.8), transparent 50%)" }} />
              <div style={{
                position: "absolute", bottom: 20, left: 32,
                fontSize: 18, fontWeight: 700, color: "#fff",
                textShadow: "0 2px 8px rgba(0,0,0,.5)",
              }}>{banner.title}</div>
            </div>
          ))}
          {banners.length > 1 && (
            <div style={{ position: "absolute", bottom: 12, right: 20, display: "flex", gap: 6 }}>
              {banners.map((_, i) => (
                <div key={i} onClick={() => setBannerIndex(i)} style={{
                  width: i === bannerIndex ? 20 : 6,
                  height: 6, borderRadius: 999,
                  background: i === bannerIndex ? "#fff" : "rgba(255,255,255,.4)",
                  cursor: "pointer", transition: "all .3s ease",
                }} />
              ))}
            </div>
          )}
        </div>
      ) : null}

      {/* 카테고리 탭 */}
      <div style={{
        display: "flex", gap: 8, padding: "16px 32px",
        overflowX: "auto",
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(9,11,20,.6)",
      }}>
        {CATEGORIES.filter(cat => cat !== "팔로우" || (token && token !== "")).map(cat => (
          <button key={cat} onClick={() => handleCategoryChange(cat)} style={{
            padding: "8px 18px", borderRadius: 999,
            border: activeCategory === cat ? "none" : "1px solid var(--border-default)",
            background: activeCategory === cat
              ? cat === "팔로우" ? "linear-gradient(135deg, #ff6b8a, #ff9532)" : "var(--gradient-cosmic)"
              : "rgba(255,255,255,.04)",
            color: activeCategory === cat ? "#fff" : cat === "팔로우" ? "#ff9af3" : "var(--text-muted)",
            fontWeight: 600, fontSize: 14, cursor: "pointer",
            whiteSpace: "nowrap", transition: "all .2s ease",
          }}>
            {cat === "팔로우" ? "💗 팔로우" : cat}
          </button>
        ))}
      </div>

      {/* 메인 콘텐츠 */}
      <div style={{ flex: 1, padding: "32px", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
        {loading ? (
          <CharacterGridSkeleton count={8} />
        ) : (
          <>
            {activeCategory === "팔로우" && (
              <section>
                <div style={{ marginBottom: 20 }}>
                  <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>💗 팔로우한 창작자 신작</h2>
                </div>
                {followFeed.length === 0 ? (
                  <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "60px 0" }}>
                    팔로우한 창작자의 새 캐릭터가 없어요.
                  </div>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 20 }}>
                    {followFeed.map(char => (
                      <CharacterCard key={char.id} character={char} onClick={() => onSelectCharacter(char)} />
                    ))}
                  </div>
                )}
              </section>
            )}

            {activeCategory !== "팔로우" && (
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

                  <div ref={observerRef} style={{ height: 40, display: "flex", alignItems: "center", justifyContent: "center", marginTop: 20 }}>
                    {loadingMore && <div style={{ color: "var(--text-muted)", fontSize: 13 }}>불러오는 중...</div>}
                    {!hasMore && characters.length > 0 && (
                      <div style={{ color: "var(--text-muted)", fontSize: 13 }}>모든 캐릭터를 불러왔어요.</div>
                    )}
                  </div>
                </section>
              </>
            )}
          </>
        )}
      </div>

      {showCoinModal && token && (
        <CoinModal apiUrl={apiUrl} token={token} onClose={() => setShowCoinModal(false)} onCoinsUpdated={(balance) => setCoins(balance)} />
      )}
      {showNotification && token && (
        <NotificationModal apiUrl={apiUrl} token={token} onClose={() => setShowNotification(false)} />
      )}
    </div>
  );
}

function CharacterCard({ character, onClick }: { character: Character; onClick: () => void }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        borderRadius: 20, overflow: "hidden",
        cursor: "pointer",
        border: "1px solid var(--border-default)",
        background: "rgba(17,21,40,.7)",
        backdropFilter: "blur(16px)", minWidth: 180,
        transform: hovered ? "translateY(-4px)" : "translateY(0)",
        boxShadow: hovered ? "0 8px 30px rgba(139,124,255,.2)" : "none",
        transition: "all .2s ease",
      }}
    >
      <div style={{ position: "relative", height: 200, overflow: "hidden" }}>
      {character.avatar ? (
      <LazyImage
        src={character.avatar}
        alt={character.name}
        fallback={character.name[0]}
        style={{
            width: "100%", height: "100%",
            transform: hovered ? "scale(1.05)" : "scale(1)",
            transition: "transform .3s ease",
          }}
        />
        ) : (
          <div style={{
            width: "100%", height: "100%",
            background: "var(--gradient-cosmic)",
            display: "grid", placeItems: "center",
            fontSize: 64, fontWeight: 700,
          }}>{character.name[0]}</div>
        )}
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(9,11,20,.9), transparent 50%)" }} />

        {/* 호버 통계 오버레이 */}
        {hovered && (
          <div style={{
            position: "absolute", inset: 0,
            background: "rgba(9,11,20,.75)",
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            gap: 16, backdropFilter: "blur(4px)",
          }}>
            <div style={{ display: "flex", gap: 20 }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22 }}>♥</div>
                <div style={{ fontSize: 14, color: "#ff6b8a", fontWeight: 700 }}>
                  {character.like_count?.toLocaleString() ?? 0}
                </div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.5)" }}>좋아요</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22 }}>💬</div>
                <div style={{ fontSize: 14, color: "#5fd6ff", fontWeight: 700 }}>
                  {character.chat_count?.toLocaleString() ?? 0}
                </div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.5)" }}>대화수</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22 }}>👁</div>
                <div style={{ fontSize: 14, color: "#ffc850", fontWeight: 700 }}>
                  {character.view_count?.toLocaleString() ?? 0}
                </div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.5)" }}>조회수</div>
              </div>
            </div>
            <div style={{
              padding: "8px 20px", borderRadius: 999,
              background: "var(--gradient-cosmic)",
              color: "#fff", fontSize: 13, fontWeight: 600,
            }}>대화하기 →</div>
          </div>
        )}
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