import { useState, useEffect } from "react";
import axios from "axios";
import type { Character } from "../App";

interface SearchPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
  onSelectCharacter: (char: Character) => void;
}

const RECENT_KEY = "stellia_recent_searches";
const CATEGORIES = ["전체", "로맨스", "판타지", "액션", "일상", "공포", "SF", "BL", "GL", "기타"];
const SORT_OPTIONS = [
  { label: "인기순", value: "popular" },
  { label: "최신순", value: "latest" },
  { label: "오래된순", value: "oldest" },
  { label: "대화 많은 순", value: "chat" },
  { label: "조회수", value: "view" },
];

const formatChar = (c: any): Character => ({
  id: c.id, name: c.name,
  title: c.description || "",
  avatar: c.image_url || "",
  description: c.description || "",
  online: true, tags: c.tags || [],
  user_id: c.user_id,
  first_message: c.first_message || "",
});

export default function SearchPage({ apiUrl, token, onBack, onSelectCharacter }: SearchPageProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Character[]>([]);
  const [ranking, setRanking] = useState<Character[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);
  const [activeCategory, setActiveCategory] = useState("전체");
  const [sortBy, setSortBy] = useState("popular");

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    const saved = localStorage.getItem(RECENT_KEY);
    if (saved) setRecentSearches(JSON.parse(saved));
    fetchRanking();
  }, []);

  const fetchRanking = async () => {
    try {
      const res = await axios.get(`${apiUrl}/characters/ranking?limit=10`, { headers });
      setRanking(res.data.map(formatChar));
    } catch { console.error("랭킹 로드 실패"); }
  };

  const saveRecentSearch = (q: string) => {
    const updated = [q, ...recentSearches.filter(s => s !== q)].slice(0, 10);
    setRecentSearches(updated);
    localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
  };

  const handleSearch = async (q: string, category?: string, sort?: string) => {
    if (!q.trim() && (category === "전체" || !category)) return;
    setQuery(q);
    setSearching(true);
    if (q.trim()) saveRecentSearch(q.trim());

    try {
      const cat = category ?? activeCategory;
      const s = sort ?? sortBy;
      let url = "";

      if (q.trim()) {
        url = `${apiUrl}/characters/search?q=${encodeURIComponent(q)}&sort=${s}`;
        if (cat !== "전체") url += `&tag=${encodeURIComponent(cat)}`;
      } else {
        url = `${apiUrl}/characters?tag=${encodeURIComponent(cat)}&sort=${s}&size=30`;
      }

      const res = await axios.get(url, { headers });
      setResults(res.data.map(formatChar));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    if (query.trim() || cat !== "전체") {
      handleSearch(query, cat, sortBy);
    }
  };

  const handleSortChange = (sort: string) => {
    setSortBy(sort);
    if (query.trim() || activeCategory !== "전체") {
      handleSearch(query, activeCategory, sort);
    }
  };

  const handleTagClick = (tag: string) => {
    setQuery(tag);
    handleSearch(tag, activeCategory, sortBy);
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem(RECENT_KEY);
  };

  return (
    <div style={{
      position: "relative", zIndex: 2, height: "100vh",
      display: "flex", flexDirection: "column",
      maxWidth: 680, margin: "0 auto",
      padding: "24px", overflowY: "auto",
    }}>

      {/* 검색창 */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <button onClick={onBack} style={{
          width: 40, height: 40, borderRadius: 12, flexShrink: 0,
          border: "1px solid var(--border-default)",
          background: "rgba(255,255,255,.04)",
          color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
        }}>←</button>
        <div className="glass-card" style={{ flex: 1, display: "flex", alignItems: "center", gap: 12, padding: "12px 18px", borderRadius: 16 }}>
          <span style={{ color: "var(--text-muted)", fontSize: 18 }}>🔍</span>
          <input
            style={{ flex: 1, border: "none", outline: "none", background: "transparent", color: "var(--text-primary)", fontSize: 16 }}
            placeholder="대화하고 싶은 캐릭터 찾기"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch(query)}
            autoFocus
          />
          {query && (
            <button onClick={() => { setQuery(""); setResults([]); }} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: 18 }}>×</button>
          )}
        </div>
      </div>

      {/* 카테고리 필터 */}
      <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 8, marginBottom: 12 }}>
        {CATEGORIES.map(cat => (
          <button key={cat} onClick={() => handleCategoryChange(cat)} style={{
            padding: "6px 16px", borderRadius: 999, whiteSpace: "nowrap",
            border: activeCategory === cat ? "none" : "1px solid var(--border-default)",
            background: activeCategory === cat ? "var(--gradient-cosmic)" : "rgba(255,255,255,.04)",
            color: activeCategory === cat ? "#fff" : "var(--text-muted)",
            fontWeight: 600, fontSize: 13, cursor: "pointer",
          }}>{cat}</button>
        ))}
      </div>

      {/* 정렬 옵션 */}
      {(results.length > 0 || activeCategory !== "전체") && (
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {SORT_OPTIONS.map(opt => (
            <button key={opt.value} onClick={() => handleSortChange(opt.value)} style={{
              padding: "6px 14px", borderRadius: 999,
              border: sortBy === opt.value ? "1px solid rgba(139,124,255,.6)" : "1px solid var(--border-default)",
              background: sortBy === opt.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.04)",
              color: sortBy === opt.value ? "var(--primary)" : "var(--text-muted)",
              fontWeight: 600, fontSize: 12, cursor: "pointer",
            }}>{opt.label}</button>
          ))}
        </div>
      )}

      {/* 검색 결과 */}
      {results.length > 0 && !searching && (
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16, letterSpacing: ".12em", textTransform: "uppercase" }}>
            검색 결과 {results.length}개
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {results.map(char => (
              <CharacterRow
                key={char.id}
                character={char}
                onClick={() => { onSelectCharacter(char); onBack(); }}
                onTagClick={handleTagClick}
              />
            ))}
          </div>
        </div>
      )}

      {/* 검색어 없을 때 */}
      {!query && activeCategory === "전체" && results.length === 0 && (
        <>
          {/* 최근 검색어 */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 16 }}>최근 검색어</div>
              {recentSearches.length > 0 && (
                <button onClick={clearRecentSearches} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 13, cursor: "pointer" }}>전체 삭제</button>
              )}
            </div>
            {recentSearches.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: 14, textAlign: "center", padding: "20px 0" }}>최근 검색어가 없어요.</div>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {recentSearches.map(s => (
                  <button key={s} onClick={() => handleSearch(s)} style={{
                    padding: "8px 16px", borderRadius: 999,
                    border: "1px solid var(--border-default)",
                    background: "rgba(255,255,255,.04)",
                    color: "var(--text-secondary)", fontSize: 14, cursor: "pointer",
                  }}>{s}</button>
                ))}
              </div>
            )}
          </div>

          {/* 인기 캐릭터 */}
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16 }}>인기 캐릭터</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {ranking.map((char, i) => (
                <div key={char.id} onClick={() => { onSelectCharacter(char); onBack(); }} style={{
                  display: "flex", alignItems: "center", gap: 16,
                  padding: "14px 0",
                  borderBottom: "1px solid var(--border-subtle)",
                  cursor: "pointer",
                }}>
                  <div style={{ width: 28, fontWeight: 700, fontSize: 16, color: i < 3 ? "var(--primary)" : "var(--text-muted)", flexShrink: 0 }}>{i + 1}</div>
                  <div style={{ width: 40, height: 40, borderRadius: "50%", background: char.avatar ? "none" : "var(--gradient-cosmic)", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 16, flexShrink: 0, overflow: "hidden" }}>
                    {char.avatar ? <img src={char.avatar} alt={char.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : char.name[0]}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600 }}>{char.name}</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{char.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* 검색 중 */}
      {searching && (
        <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px 0" }}>검색 중...</div>
      )}

      {/* 결과 없음 */}
      {!searching && (query || activeCategory !== "전체") && results.length === 0 && (
        <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px 0" }}>
          검색 결과가 없어요.
        </div>
      )}
    </div>
  );
}

function CharacterRow({ character, onClick, onTagClick }: {
  character: Character;
  onClick: () => void;
  onTagClick: (tag: string) => void;
}) {
  return (
    <div onClick={onClick} className="glass-card" style={{
      borderRadius: 18, padding: 16,
      display: "flex", alignItems: "center", gap: 14,
      cursor: "pointer", transition: "all .2s ease",
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: "50%",
        background: character.avatar ? "none" : "var(--gradient-cosmic)",
        display: "grid", placeItems: "center",
        fontWeight: 700, fontSize: 18, flexShrink: 0, overflow: "hidden",
      }}>
        {character.avatar
          ? <img src={character.avatar} alt={character.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : character.name[0]}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700 }}>{character.name}</div>
        <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 3, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{character.description}</div>
        {character.tags.length > 0 && (
          <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
            {character.tags.slice(0, 3).map(tag => (
              <span key={tag} onClick={e => { e.stopPropagation(); onTagClick(tag); }} style={{
                padding: "3px 8px", borderRadius: 999,
                background: "rgba(139,124,255,.12)",
                border: "1px solid rgba(139,124,255,.18)",
                color: "var(--primary)", fontSize: 11, cursor: "pointer",
              }}>#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}