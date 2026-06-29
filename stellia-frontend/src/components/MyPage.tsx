import { useState, useEffect } from "react";
import axios from "axios";
import CharacterImageModal from "./CharacterImageModal";

interface MyPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
  onGoAdmin: () => void;
  onEditCharacter: (characterId: string) => void;
}

const DIFFICULTY_COLOR: Record<string, string> = {
  bronze: "#cd7f32",
  silver: "#c0c0c0",
  gold: "#f6c65b",
  platinum: "#8b7cff",
  anniversary: "#ff9af3",
};

const DIFFICULTY_LABEL: Record<string, string> = {
  bronze: "브론즈",
  silver: "실버",
  gold: "골드",
  platinum: "플래티넘",
  anniversary: "기념일",
};

export default function MyPage({ apiUrl, token, onBack, onGoAdmin, onEditCharacter }: MyPageProps) {
  const [activeTab, setActiveTab] = useState<"profile" | "characters" | "likes" | "bookmarks" | "achievements" | "tokens" | "settings">("profile");
  const [user, setUser] = useState<any>(null);
  const [myCharacters, setMyCharacters] = useState<any[]>([]);
  const [likedCharacters, setLikedCharacters] = useState<any[]>([]);
  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [equipMessage, setEquipMessage] = useState("");
  const [showImageModal, setShowImageModal] = useState<string | null>(null);
  const [tokenHistory, setTokenHistory] = useState<any[]>([]);
  const [adultLoading, setAdultLoading] = useState(false);
  const [showAdultConfirm, setShowAdultConfirm] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/users/me`, { headers })
      .then(res => { setUser(res.data); setUsername(res.data.username); })
      .catch(console.error);
    axios.get(`${apiUrl}/tokens/me/history?page=1&size=20`, { headers })
      .then(res => setTokenHistory(res.data.items))
      .catch(console.error);
    axios.get(`${apiUrl}/characters/me`, { headers })
      .then(res => setMyCharacters(res.data))
      .catch(console.error);
    axios.get(`${apiUrl}/likes/me`, { headers })
      .then(res => setLikedCharacters(res.data))
      .catch(console.error);
    axios.get(`${apiUrl}/achievements/me`, { headers })
      .then(res => setAchievements(res.data))
      .catch(console.error);
    axios.get(`${apiUrl}/likes/bookmarks`, { headers })
      .then(res => setBookmarks(res.data))
      .catch(console.error);
  }, []);

  const handleUpdateProfile = async () => {
    setLoading(true);
    setMessage("");
    try {
      await axios.patch(`${apiUrl}/users/me`, { username }, { headers });
      setMessage("프로필이 수정됐어요.");
    } catch {
      setMessage("수정에 실패했어요.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCharacter = async (charId: string) => {
    if (!confirm("정말 삭제할까요?")) return;
    try {
      await axios.delete(`${apiUrl}/characters/${charId}`, { headers });
      setMyCharacters(prev => prev.filter(c => c.id !== charId));
    } catch {
      alert("삭제에 실패했어요.");
    }
  };

  const handleEquipTitle = async (prefixTitle: string, suffixTitle: string) => {
    setEquipMessage("");
    try {
      await axios.patch(`${apiUrl}/achievements/me/equip-title`, {
        prefix_title: prefixTitle,
        suffix_title: suffixTitle,
      }, { headers });
      setUser((prev: any) => ({ ...prev, equipped_prefix: prefixTitle, equipped_suffix: suffixTitle }));
      setEquipMessage("칭호가 장착됐어요!");
    } catch {
      setEquipMessage("칭호 장착에 실패했어요.");
    }
  };

  const handleAdultVerify = async () => {
    setAdultLoading(true);
    try {
      await axios.post(`${apiUrl}/users/me/adult-verify`, {}, { headers });
      setUser((prev: any) => ({ ...prev, is_adult: 1 }));
      setShowAdultConfirm(false);
      setMessage("성인 인증이 완료됐어요.");
    } catch {
      setMessage("성인 인증에 실패했어요.");
    } finally {
      setAdultLoading(false);
    }
  };

  const handleAdultCancel = async () => {
    if (!confirm("성인 인증을 해제할까요?")) return;
    setAdultLoading(true);
    try {
      await axios.delete(`${apiUrl}/users/me/adult-verify`, { headers });
      setUser((prev: any) => ({ ...prev, is_adult: 0 }));
      setMessage("성인 인증이 해제됐어요.");
    } catch {
      setMessage("해제에 실패했어요.");
    } finally {
      setAdultLoading(false);
    }
  };

  const tabs = [
    { id: "profile", label: "프로필" },
    { id: "characters", label: "내 캐릭터" },
    { id: "likes", label: "좋아요" },
    { id: "bookmarks", label: "북마크" },
    { id: "achievements", label: "업적" },
    { id: "tokens", label: "토큰 내역" },
    { id: "settings", label: "설정" },
  ] as const;

  const inputStyle = {
    padding: "14px 18px", borderRadius: 14,
    border: "1px solid var(--border-default)",
    background: "rgba(255,255,255,.04)",
    color: "var(--text-primary)", fontSize: 15,
    outline: "none", width: "100%",
    boxSizing: "border-box" as const,
  };

  const achievedList = achievements.filter(a => a.achieved);

  return (
    <div style={{
      position: "relative", zIndex: 2, height: "100vh",
      display: "flex", flexDirection: "column",
      maxWidth: 680, margin: "0 auto",
      padding: "24px", overflowY: "auto",
    }}>

      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28 }}>
        <button onClick={onBack} style={{
          width: 40, height: 40, borderRadius: 12,
          border: "1px solid var(--border-default)",
          background: "rgba(255,255,255,.04)",
          color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
        }}>←</button>
        <div style={{
          fontSize: 22, fontWeight: 700,
          background: "var(--gradient-cosmic)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}>마이페이지</div>
      </div>

      <div style={{
        display: "flex", borderRadius: 16,
        background: "rgba(255,255,255,.04)",
        border: "1px solid var(--border-default)",
        overflow: "hidden", marginBottom: 24,
      }}>
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            flex: 1, padding: "12px", border: "none",
            background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
            color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
            fontWeight: 600, fontSize: 12, transition: "all .2s ease", cursor: "pointer",
          }}>{tab.label}</button>
        ))}
      </div>

      {activeTab === "profile" && (
        <div className="glass-card" style={{ borderRadius: 24, padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
            <div style={{
              width: 80, height: 80, borderRadius: "50%",
              background: "var(--gradient-cosmic)",
              display: "grid", placeItems: "center",
              fontSize: 32, fontWeight: 700,
              boxShadow: "var(--shadow-glow-primary)",
              overflow: "hidden",
            }}>
              {user?.profile_image_url ? (
                <img src={user.profile_image_url} alt={username}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              ) : username[0]?.toUpperCase()}
            </div>
            <div>
              <div style={{ fontSize: 13, color: "var(--primary)", marginBottom: 4 }}>
                {user?.equipped_prefix && <span>[{user.equipped_prefix}] </span>}
                <span style={{ fontWeight: 700, fontSize: 18, color: "var(--text-primary)" }}>{user?.username}</span>
                {user?.equipped_suffix && <span> [{user.equipped_suffix}]</span>}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: 14 }}>{user?.email}</div>
              <div style={{ color: "var(--gold)", fontSize: 13, marginTop: 4 }}>
                ✦ {user?.token_balance?.toLocaleString()} 럭키 코인
              </div>
              {user?.is_adult === 1 && (
                <div style={{
                  display: "inline-block", marginTop: 6,
                  padding: "2px 10px", borderRadius: 999, fontSize: 11,
                  background: "rgba(255,107,138,.15)",
                  border: "1px solid rgba(255,107,138,.3)",
                  color: "#ff6b8a",
                }}>🔞 성인 인증 완료</div>
              )}
            </div>
          </div>

          <div>
            <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>프로필 이미지</label>
            <input type="file" accept="image/*" id="profile-image-input" style={{ display: "none" }}
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const formData = new FormData();
                formData.append("file", file);
                try {
                  const res = await axios.post(`${apiUrl}/users/me/profile-image`, formData, {
                    headers: { ...headers, "Content-Type": "multipart/form-data" }
                  });
                  setUser((prev: any) => ({ ...prev, profile_image_url: res.data.image_url }));
                  setMessage("프로필 이미지가 변경됐어요.");
                } catch {
                  setMessage("이미지 업로드에 실패했어요.");
                }
              }}
            />
            <label htmlFor="profile-image-input" style={{
              display: "inline-block",
              padding: "10px 18px", borderRadius: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", fontSize: 13, cursor: "pointer",
            }}>🖼 이미지 변경</label>
          </div>

          <div>
            <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>닉네임 수정</label>
            <input style={inputStyle} value={username} onChange={e => setUsername(e.target.value)} placeholder="새 닉네임" />
          </div>

          {message && (
            <div style={{ color: message.includes("실패") ? "#ff6b8a" : "#49d89a", fontSize: 13 }}>{message}</div>
          )}

          <button onClick={handleUpdateProfile} disabled={loading} style={{
            padding: "14px", borderRadius: 14, border: "none",
            background: "var(--gradient-cosmic)",
            color: "#fff", fontWeight: 700, fontSize: 15,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
          }}>{loading ? "저장 중..." : "저장"}</button>
        </div>
      )}

      {activeTab === "characters" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {myCharacters.length === 0 ? (
            <div className="glass-card" style={{ borderRadius: 24, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              아직 만든 캐릭터가 없어요.
            </div>
          ) : myCharacters.map(char => (
            <div key={char.id} className="glass-card" style={{ borderRadius: 20, padding: 18, display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{
                width: 52, height: 52, borderRadius: "50%",
                background: char.image_url ? "none" : "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontWeight: 700, fontSize: 20, flexShrink: 0, overflow: "hidden",
              }}>
                {char.image_url
                  ? <img src={char.image_url} alt={char.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  : char.name[0]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700 }}>{char.name}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
                  {char.visibility === "public" ? "공개" : "비공개"} · 대화 {char.chat_count}회
                </div>
              </div>
              <button onClick={() => onEditCharacter(char.id)} style={{
                padding: "8px 14px", borderRadius: 10,
                border: "1px solid rgba(255,200,80,.3)",
                background: "rgba(255,200,80,.08)",
                color: "#ffc850", fontSize: 13, cursor: "pointer",
              }}>✏ 수정</button>
              <button onClick={() => setShowImageModal(char.id)} style={{
                padding: "8px 14px", borderRadius: 10,
                border: "1px solid rgba(95,214,255,.3)",
                background: "rgba(95,214,255,.08)",
                color: "var(--secondary)", fontSize: 13, cursor: "pointer",
              }}>🖼 이미지</button>
              <button onClick={() => handleDeleteCharacter(char.id)} style={{
                padding: "8px 14px", borderRadius: 10,
                border: "1px solid rgba(255,107,138,.3)",
                background: "rgba(255,107,138,.08)",
                color: "#ff6b8a", fontSize: 13, cursor: "pointer",
              }}>삭제</button>
            </div>
          ))}
        </div>
      )}

      {activeTab === "likes" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {likedCharacters.length === 0 ? (
            <div className="glass-card" style={{ borderRadius: 24, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              좋아요한 캐릭터가 없어요.
            </div>
          ) : likedCharacters.map(char => (
            <div key={char.id} className="glass-card" style={{ borderRadius: 20, padding: 18, display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{
                width: 52, height: 52, borderRadius: "50%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontWeight: 700, fontSize: 20, flexShrink: 0,
              }}>{char.name?.[0]}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700 }}>{char.name}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>{char.description}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "bookmarks" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {bookmarks.length === 0 ? (
            <div className="glass-card" style={{ borderRadius: 24, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              북마크한 캐릭터가 없어요.
            </div>
          ) : bookmarks.map(char => (
            <div key={char.id} className="glass-card" style={{ borderRadius: 20, padding: 18, display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{
                width: 52, height: 52, borderRadius: "50%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontWeight: 700, fontSize: 20, flexShrink: 0, overflow: "hidden",
              }}>
                {char.image_url
                  ? <img src={char.image_url} alt={char.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  : char.name[0]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700 }}>{char.name}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>{char.description}</div>
              </div>
              <span style={{ color: "#ffc850", fontSize: 20 }}>★</span>
            </div>
          ))}
        </div>
      )}

      {activeTab === "achievements" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="glass-card" style={{ borderRadius: 20, padding: 20 }}>
            <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>달성 현황</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>
              {achievedList.length} <span style={{ color: "var(--text-muted)", fontSize: 14 }}>/ {achievements.length}</span>
            </div>
            <div style={{ marginTop: 10, height: 6, borderRadius: 999, background: "var(--border-default)", overflow: "hidden" }}>
              <div style={{
                height: "100%",
                width: `${achievements.length ? (achievedList.length / achievements.length) * 100 : 0}%`,
                background: "var(--gradient-cosmic)", borderRadius: 999, transition: "width .5s ease",
              }} />
            </div>
          </div>

          {achievedList.length > 0 && (
            <div className="glass-card" style={{ borderRadius: 20, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase" }}>칭호 장착</div>
              <div style={{ fontSize: 15, fontWeight: 600, textAlign: "center" }}>
                {user?.equipped_prefix && <span style={{ color: "var(--primary)" }}>[{user.equipped_prefix}] </span>}
                <span>{user?.username}</span>
                {user?.equipped_suffix && <span style={{ color: "var(--primary)" }}> [{user.equipped_suffix}]</span>}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 8 }}>앞 칭호</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 150, overflowY: "auto" }}>
                    <button onClick={() => handleEquipTitle("", user?.equipped_suffix ?? "")} style={{
                      padding: "8px 12px", borderRadius: 10, fontSize: 13,
                      border: !user?.equipped_prefix ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: !user?.equipped_prefix ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                      color: !user?.equipped_prefix ? "var(--primary)" : "var(--text-muted)", cursor: "pointer",
                    }}>없음</button>
                    {achievedList.filter(a => a.prefix_title).map(a => (
                      <button key={a.code} onClick={() => handleEquipTitle(a.prefix_title, user?.equipped_suffix ?? "")} style={{
                        padding: "8px 12px", borderRadius: 10, fontSize: 13,
                        border: user?.equipped_prefix === a.prefix_title ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                        background: user?.equipped_prefix === a.prefix_title ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                        color: user?.equipped_prefix === a.prefix_title ? "var(--primary)" : "var(--text-muted)", cursor: "pointer",
                      }}>[{a.prefix_title}]</button>
                    ))}
                  </div>
                </div>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 8 }}>뒤 칭호</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 150, overflowY: "auto" }}>
                    <button onClick={() => handleEquipTitle(user?.equipped_prefix ?? "", "")} style={{
                      padding: "8px 12px", borderRadius: 10, fontSize: 13,
                      border: !user?.equipped_suffix ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: !user?.equipped_suffix ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                      color: !user?.equipped_suffix ? "var(--primary)" : "var(--text-muted)", cursor: "pointer",
                    }}>없음</button>
                    {achievedList.filter(a => a.suffix_title).map(a => (
                      <button key={a.code} onClick={() => handleEquipTitle(user?.equipped_prefix ?? "", a.suffix_title)} style={{
                        padding: "8px 12px", borderRadius: 10, fontSize: 13,
                        border: user?.equipped_suffix === a.suffix_title ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                        background: user?.equipped_suffix === a.suffix_title ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                        color: user?.equipped_suffix === a.suffix_title ? "var(--primary)" : "var(--text-muted)", cursor: "pointer",
                      }}>[{a.suffix_title}]</button>
                    ))}
                  </div>
                </div>
              </div>
              {equipMessage && (
                <div style={{ color: equipMessage.includes("실패") ? "#ff6b8a" : "#49d89a", fontSize: 13, textAlign: "center" }}>{equipMessage}</div>
              )}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {achievements.map(a => (
              <div key={a.code} className="glass-card" style={{ borderRadius: 16, padding: 16, display: "flex", alignItems: "center", gap: 14, opacity: a.achieved ? 1 : 0.5 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12, flexShrink: 0,
                  background: a.achieved ? `${DIFFICULTY_COLOR[a.difficulty]}22` : "rgba(255,255,255,.04)",
                  border: `1px solid ${a.achieved ? DIFFICULTY_COLOR[a.difficulty] : "var(--border-default)"}`,
                  display: "grid", placeItems: "center", fontSize: 20,
                }}>{a.achieved ? "✦" : "?"}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{a.title}</span>
                    <span style={{
                      padding: "2px 8px", borderRadius: 999, fontSize: 11,
                      background: `${DIFFICULTY_COLOR[a.difficulty]}22`,
                      color: DIFFICULTY_COLOR[a.difficulty],
                      border: `1px solid ${DIFFICULTY_COLOR[a.difficulty]}44`,
                    }}>{DIFFICULTY_LABEL[a.difficulty]}</span>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 3 }}>{a.description}</div>
                  {(a.prefix_title || a.suffix_title) && (
                    <div style={{ marginTop: 4, fontSize: 11, color: "var(--primary)" }}>
                      칭호: {a.prefix_title && `[${a.prefix_title}]`} {a.suffix_title && `[${a.suffix_title}]`}
                    </div>
                  )}
                </div>
                <div style={{ color: "var(--gold)", fontSize: 13, fontWeight: 600, flexShrink: 0 }}>+{a.reward_token.toLocaleString()} 🥈</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "tokens" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="glass-card" style={{ borderRadius: 20, padding: 20, display: "flex", gap: 20 }}>
            <div style={{ flex: 1, textAlign: "center" }}>
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>금화</div>
              <div style={{ color: "#ffc850", fontWeight: 700, fontSize: 20 }}>✦ {user?.token_purchased?.toLocaleString() ?? 0}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 4 }}>무제한</div>
            </div>
            <div style={{ width: 1, background: "var(--border-subtle)" }} />
            <div style={{ flex: 1, textAlign: "center" }}>
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>은화</div>
              <div style={{ color: "#c0c0c0", fontWeight: 700, fontSize: 20 }}>🥈 {user?.token_event?.toLocaleString() ?? 0}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 4 }}>21일 만료</div>
            </div>
          </div>
          {tokenHistory.length === 0 ? (
            <div className="glass-card" style={{ borderRadius: 20, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>토큰 내역이 없어요.</div>
          ) : tokenHistory.map(h => (
            <div key={h.id} className="glass-card" style={{ borderRadius: 16, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{h.reason}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 3 }}>
                  {new Date(h.created_at).toLocaleDateString("ko-KR")}
                  {h.expires_at && <span style={{ marginLeft: 8, color: "#ff9532" }}>만료: {new Date(h.expires_at).toLocaleDateString("ko-KR")}</span>}
                </div>
              </div>
              <div style={{ fontWeight: 700, fontSize: 16, color: h.amount > 0 ? "#49d89a" : "#ff6b8a" }}>
                {h.amount > 0 ? "+" : ""}{h.amount.toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "settings" && (
        <div className="glass-card" style={{ borderRadius: 24, padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>🔞 성인 인증</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16, lineHeight: 1.6 }}>
              성인 인증 시 19금 캐릭터와 콘텐츠에 접근할 수 있어요.<br />
              <span style={{ fontSize: 12, color: "#ff9532" }}>※ 현재 자기선언 방식 — 사업자등록 후 본인인증으로 교체 예정</span>
            </div>
            {user?.is_adult === 1 ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 18px", borderRadius: 14, border: "1px solid rgba(255,107,138,.3)", background: "rgba(255,107,138,.06)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 20 }}>🔞</span>
                  <div>
                    <div style={{ fontWeight: 600, color: "#ff6b8a" }}>성인 인증 완료</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 2 }}>19금 콘텐츠 접근 가능</div>
                  </div>
                </div>
                <button onClick={handleAdultCancel} disabled={adultLoading} style={{
                  padding: "8px 14px", borderRadius: 10, fontSize: 13,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-muted)", cursor: "pointer",
                }}>인증 해제</button>
              </div>
            ) : (
              <button onClick={() => setShowAdultConfirm(true)} style={{
                width: "100%", padding: "14px", borderRadius: 14,
                border: "1px solid rgba(255,107,138,.3)",
                background: "rgba(255,107,138,.08)",
                color: "#ff6b8a", fontWeight: 600, fontSize: 15, cursor: "pointer",
              }}>🔞 성인 인증하기</button>
            )}
          </div>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>기본 출력량</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}>AI 응답의 기본 길이를 설정해요.</div>
            <div style={{ display: "flex", gap: 10 }}>
              {[
                { label: "짧게", value: "short", tokens: "300토큰" },
                { label: "보통", value: "medium", tokens: "1,000토큰" },
                { label: "길게", value: "long", tokens: "2,000토큰" },
              ].map(opt => (
                <button key={opt.value} onClick={async () => {
                  await axios.patch(`${apiUrl}/users/me/settings`, { output_length: opt.value }, { headers });
                  setUser((prev: any) => ({ ...prev, output_length: opt.value }));
                }} style={{
                  flex: 1, padding: "12px 8px", borderRadius: 14,
                  border: user?.output_length === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                  background: user?.output_length === opt.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                  color: user?.output_length === opt.value ? "var(--primary)" : "var(--text-muted)",
                  fontWeight: 600, cursor: "pointer",
                  display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
                }}>
                  <span style={{ fontSize: 14 }}>{opt.label}</span>
                  <span style={{ fontSize: 11, opacity: .7 }}>{opt.tokens}</span>
                </button>
              ))}
            </div>
            <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>
              ※ 메모리 패스 구매 시 출력량 배수(x1.5, x2.0)를 설정할 수 있어요.
            </div>
          </div>

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>세이프티 모드</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}>부적절한 콘텐츠를 필터링해요.</div>
            <div style={{ display: "flex", gap: 10 }}>
              {[{ label: "켜기", value: 1 }, { label: "끄기", value: 0 }].map(opt => (
                <button key={opt.value} onClick={async () => {
                  await axios.patch(`${apiUrl}/users/me/settings`, { safety_mode: opt.value }, { headers });
                  setUser((prev: any) => ({ ...prev, safety_mode: opt.value }));
                }} style={{
                  flex: 1, padding: "12px", borderRadius: 14,
                  border: user?.safety_mode === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                  background: user?.safety_mode === opt.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                  color: user?.safety_mode === opt.value ? "var(--primary)" : "var(--text-muted)",
                  fontWeight: 600, cursor: "pointer",
                }}>{opt.label}</button>
              ))}
            </div>
          </div>

          {user?.is_admin === 1 && (
            <div>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>관리자</div>
              <button onClick={onGoAdmin} style={{
                width: "100%", padding: "14px", borderRadius: 14,
                border: "1px solid rgba(255,107,138,.3)",
                background: "rgba(255,107,138,.08)",
                color: "#ff6b8a", fontWeight: 600, cursor: "pointer",
              }}>관리자 패널</button>
            </div>
          )}

          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>회원 탈퇴</div>
            <button onClick={async () => {
              if (!confirm("정말 탈퇴할까요? 모든 데이터가 삭제돼요.")) return;
              await axios.delete(`${apiUrl}/users/me`, { headers });
              window.location.reload();
            }} style={{
              width: "100%", padding: "14px", borderRadius: 14,
              border: "1px solid rgba(255,107,138,.3)",
              background: "rgba(255,107,138,.08)",
              color: "#ff6b8a", fontWeight: 600, cursor: "pointer",
            }}>회원 탈퇴</button>
          </div>
        </div>
      )}

      {showImageModal && (
        <CharacterImageModal
          apiUrl={apiUrl}
          token={token}
          characterId={showImageModal}
          characterName={myCharacters.find(c => c.id === showImageModal)?.name ?? ""}
          onClose={() => setShowImageModal(null)}
        />
      )}

      {showAdultConfirm && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.7)", display: "grid", placeItems: "center", zIndex: 100 }}>
          <div style={{
            borderRadius: 24, padding: 32,
            background: "rgba(17,21,40,.98)",
            border: "1px solid rgba(255,107,138,.3)",
            width: 380, maxWidth: "90vw",
          }}>
            <div style={{ fontSize: 32, textAlign: "center", marginBottom: 16 }}>🔞</div>
            <div style={{ fontWeight: 700, fontSize: 18, textAlign: "center", marginBottom: 12 }}>성인 인증</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, textAlign: "center", lineHeight: 1.7, marginBottom: 24 }}>
              본인이 만 18세 이상임을 확인합니다.<br />
              미성년자가 성인 콘텐츠에 접근하는 것은<br />
              법적으로 금지되어 있습니다.<br />
              <span style={{ color: "#ff9532", fontSize: 12, marginTop: 8, display: "block" }}>
                ※ 추후 실명 본인인증으로 교체될 예정입니다.
              </span>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setShowAdultConfirm(false)} style={{
                flex: 1, padding: "14px", borderRadius: 14,
                border: "1px solid var(--border-default)",
                background: "none", color: "var(--text-muted)",
                fontWeight: 600, cursor: "pointer",
              }}>취소</button>
              <button onClick={handleAdultVerify} disabled={adultLoading} style={{
                flex: 1, padding: "14px", borderRadius: 14, border: "none",
                background: "linear-gradient(135deg, #ff6b8a, #ff9532)",
                color: "#fff", fontWeight: 700, cursor: "pointer",
                opacity: adultLoading ? 0.7 : 1,
              }}>
                {adultLoading ? "처리 중..." : "만 18세 이상입니다"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}