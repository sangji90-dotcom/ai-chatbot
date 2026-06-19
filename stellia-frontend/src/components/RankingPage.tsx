import { useState, useEffect } from "react";
import axios from "axios";
import type { Character } from "../App";

interface RankingPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
  onSelectCharacter: (char: Character) => void;
}

const PERIODS = [
  { label: "전체", value: "all" },
  { label: "이번 달", value: "monthly" },
  { label: "이번 주", value: "weekly" },
];

const SORT_OPTIONS = [
  { label: "좋아요순", value: "popular" },
  { label: "대화 많은 순", value: "chat" },
  { label: "조회수순", value: "view" },
  { label: "최신순", value: "latest" },
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

export default function RankingPage({ apiUrl, token, onBack, onSelectCharacter }: RankingPageProps) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [activePeriod, setActivePeriod] = useState("all");
  const [activeSort, setActiveSort] = useState("popular");

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    fetchRanking();
  }, [activePeriod, activeSort]);

  const fetchRanking = async () => {
    setLoading(true);
    try {
      const res = await axios.get(
        `${apiUrl}/characters/ranking?limit=50&sort=${activeSort}&period=${activePeriod}`,
        { headers }
      );
      setCharacters(res.data.map(formatChar));
    } catch {
      console.error("랭킹 로드 실패");
    } finally {
      setLoading(false);
    }
  };

  const RANK_COLORS = ["#ffc850", "#c0c0c0", "#cd7f32"];
  const RANK_LABELS = ["🥇", "🥈", "🥉"];

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
        <button onClick={onBack} style={{
          background: "none", border: "none",
          color: "var(--text-muted)", fontSize: 22, cursor: "pointer",
        }}>←</button>
        <span style={{
          fontSize: 20, fontWeight: 700,
          background: "var(--gradient-cosmic)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}>랭킹</span>
      </nav>

      <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px" }}>

        {/* 기간 필터 */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {PERIODS.map(p => (
            <button key={p.value} onClick={() => setActivePeriod(p.value)} style={{
              padding: "8px 20px", borderRadius: 999,
              border: activePeriod === p.value ? "none" : "1px solid var(--border-default)",
              background: activePeriod === p.value ? "var(--gradient-cosmic)" : "rgba(255,255,255,.04)",
              color: activePeriod === p.value ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 14, cursor: "pointer",
            }}>{p.label}</button>
          ))}
        </div>

        {/* 정렬 옵션 */}
        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          {SORT_OPTIONS.map(s => (
            <button key={s.value} onClick={() => setActiveSort(s.value)} style={{
              padding: "6px 14px", borderRadius: 999,
              border: activeSort === s.value ? "1px solid rgba(139,124,255,.6)" : "1px solid var(--border-default)",
              background: activeSort === s.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.04)",
              color: activeSort === s.value ? "var(--primary)" : "var(--text-muted)",
              fontWeight: 600, fontSize: 12, cursor: "pointer",
            }}>{s.label}</button>
          ))}
        </div>

        {/* 상위 3개 podium */}
        {!loading && characters.length >= 3 && (
          <div style={{ display: "flex", gap: 12, marginBottom: 32, alignItems: "flex-end" }}>
            {[1, 0, 2].map(i => (
              <div key={i} onClick={() => onSelectCharacter(characters[i])} style={{
                flex: i === 0 ? 1.2 : 1,
                borderRadius: 20,
                border: `1px solid ${i === 0 ? "rgba(255,200,80,.4)" : "var(--border-default)"}`,
                background: i === 0 ? "rgba(255,200,80,.08)" : "rgba(17,21,40,.7)",
                padding: "20px 16px",
                textAlign: "center",
                cursor: "pointer",
                transition: "all .2s ease",
              }}>
                <div style={{ fontSize: 28, marginBottom: 12 }}>{RANK_LABELS[i]}</div>
                <div style={{
                  width: i === 0 ? 72 : 56, height: i === 0 ? 72 : 56,
                  borderRadius: "50%",
                  background: characters[i].avatar ? "none" : "var(--gradient-cosmic)",
                  margin: "0 auto 12px",
                  overflow: "hidden",
                  display: "grid", placeItems: "center",
                  fontWeight: 700, fontSize: i === 0 ? 28 : 22,
                  border: `2px solid ${RANK_COLORS[i]}`,
                }}>
                  {characters[i].avatar
                    ? <img src={characters[i].avatar} alt={characters[i].name}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    : characters[i].name[0]}
                </div>
                <div style={{ fontWeight: 700, fontSize: i === 0 ? 15 : 13, marginBottom: 4 }}>{characters[i].name}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {characters[i].description}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 나머지 순위 */}
        {loading ? (
          <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px 0" }}>불러오는 중...</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {characters.slice(3).map((char, i) => (
              <div key={char.id} onClick={() => onSelectCharacter(char)} style={{
                display: "flex", alignItems: "center", gap: 16,
                padding: "14px 16px", borderRadius: 16,
                border: "1px solid var(--border-subtle)",
                background: "rgba(17,21,40,.5)",
                cursor: "pointer", transition: "all .2s ease",
              }}>
                <div style={{
                  width: 32, fontWeight: 700, fontSize: 15,
                  color: "var(--text-muted)", flexShrink: 0, textAlign: "center",
                }}>{i + 4}</div>
                <div style={{
                  width: 44, height: 44, borderRadius: "50%",
                  background: char.avatar ? "none" : "var(--gradient-cosmic)",
                  display: "grid", placeItems: "center",
                  fontWeight: 700, fontSize: 18, flexShrink: 0, overflow: "hidden",
                }}>
                  {char.avatar
                    ? <img src={char.avatar} alt={char.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    : char.name[0]}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{char.name}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {char.description}
                  </div>
                </div>
                {char.tags.slice(0, 2).map(tag => (
                  <span key={tag} style={{
                    padding: "3px 8px", borderRadius: 999,
                    background: "rgba(139,124,255,.12)",
                    border: "1px solid rgba(139,124,255,.18)",
                    color: "var(--primary)", fontSize: 11, flexShrink: 0,
                  }}>#{tag}</span>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}