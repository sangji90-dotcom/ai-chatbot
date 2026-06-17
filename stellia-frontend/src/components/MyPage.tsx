import { useState, useEffect } from "react";
import axios from "axios";
import CharacterImageModal from "./CharacterImageModal";

interface MyPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
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

export default function MyPage({ apiUrl, token, onBack }: MyPageProps) {
  const [activeTab, setActiveTab] = useState<"profile" | "characters" | "likes" | "achievements" | "settings">("profile");
  const [user, setUser] = useState<any>(null);
  const [myCharacters, setMyCharacters] = useState<any[]>([]);
  const [likedCharacters, setLikedCharacters] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [equipMessage, setEquipMessage] = useState("");
  const [showImageModal, setShowImageModal] = useState<string | null>(null);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/users/me`, { headers })
      .then(res => { setUser(res.data); setUsername(res.data.username); })
      .catch(console.error);

    axios.get(`${apiUrl}/characters/me`, { headers })
      .then(res => setMyCharacters(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/likes`, { headers })
      .then(res => setLikedCharacters(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/achievements/me`, { headers })
      .then(res => setAchievements(res.data))
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

  const tabs = [
    { id: "profile", label: "프로필" },
    { id: "characters", label: "내 캐릭터" },
    { id: "likes", label: "좋아요" },
    { id: "achievements", label: "업적" },
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
    <div
      style={{
        position: "relative", zIndex: 2, height: "100vh",
        display: "flex", flexDirection: "column",
        maxWidth: 680, margin: "0 auto",
        padding: "24px", overflowY: "auto",
      }}
    >
      {/* 헤더 */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28 }}>
        <button
          onClick={onBack}
          style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
          }}
        >
          ←
        </button>
        <div
          style={{
            fontSize: 22, fontWeight: 700,
            background: "var(--gradient-cosmic)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          마이페이지
        </div>
      </div>

      {/* 탭 */}
      <div
        style={{
          display: "flex", borderRadius: 16,
          background: "rgba(255,255,255,.04)",
          border: "1px solid var(--border-default)",
          overflow: "hidden", marginBottom: 24,
        }}
      >
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1, padding: "12px", border: "none",
              background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 12, transition: "all .2s ease", cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 프로필 탭 */}
      {activeTab === "profile" && (
        <div className="glass-card" style={{ borderRadius: 24, padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
            <div
              style={{
                width: 80, height: 80, borderRadius: "50%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontSize: 32, fontWeight: 700,
                boxShadow: "var(--shadow-glow-primary)",
              }}
            >
              {username[0]?.toUpperCase()}
            </div>
            <div>
              {/* 칭호 + 닉네임 표시 */}
              <div style={{ fontSize: 13, color: "var(--primary)", marginBottom: 4 }}>
                {user?.equipped_prefix && <span>[{user.equipped_prefix}] </span>}
                <span style={{ fontWeight: 700, fontSize: 18, color: "var(--text-primary)" }}>{user?.username}</span>
                {user?.equipped_suffix && <span> [{user.equipped_suffix}]</span>}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: 14 }}>{user?.email}</div>
              <div style={{ color: "var(--gold)", fontSize: 13, marginTop: 4 }}>
                ✦ {user?.token_balance?.toLocaleString()} 럭키 코인
              </div>
            </div>
          </div>

          <div>
            <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>닉네임 수정</label>
            <input style={inputStyle} value={username} onChange={e => setUsername(e.target.value)} placeholder="새 닉네임" />
          </div>

          {message && (
            <div style={{ color: message.includes("실패") ? "#ff6b8a" : "#49d89a", fontSize: 13 }}>
              {message}
            </div>
          )}

          <button
            onClick={handleUpdateProfile}
            disabled={loading}
            style={{
              padding: "14px", borderRadius: 14, border: "none",
              background: "var(--gradient-cosmic)",
              color: "#fff", fontWeight: 700, fontSize: 15,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "저장 중..." : "저장"}
          </button>
        </div>
      )}

      {/* 내 캐릭터 탭 */}
      {activeTab === "characters" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {myCharacters.length === 0 ? (
            <div className="glass-card" style={{ borderRadius: 24, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              아직 만든 캐릭터가 없어요.
            </div>
          ) : (
            myCharacters.map(char => (
              <div key={char.id} className="glass-card" style={{ borderRadius: 20, padding: 18, display: "flex", alignItems: "center", gap: 16 }}>
                <div
                  style={{
                    width: 52, height: 52, borderRadius: "50%",
                    background: char.image_url ? "none" : "var(--gradient-cosmic)",
                    display: "grid", placeItems: "center",
                    fontWeight: 700, fontSize: 20, flexShrink: 0, overflow: "hidden",
                  }}
                >
                  {char.image_url
                    ? <img src={char.image_url} alt={char.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    : char.name[0]
                  }
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700 }}>{char.name}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
                    {char.visibility === "public" ? "공개" : "비공개"} · 대화 {char.chat_count}회
                  </div>
                </div>
                <button
                   onClick={() => setShowImageModal(char.id)}
                    style={{
                    padding: "8px 14px", borderRadius: 10,
                    border: "1px solid rgba(95,214,255,.3)",
                    background: "rgba(95,214,255,.08)",
                    color: "var(--secondary)", fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                🖼 이미지
                </button>
                <button
            onClick={() => handleDeleteCharacter(char.id)}
              style={{
                    padding: "8px 14px", borderRadius: 10,
                    border: "1px solid rgba(255,107,138,.3)",
                    background: "rgba(255,107,138,.08)",
                    color: "#ff6b8a", fontSize: 13, cursor: "pointer",
                  }}
                >
                    삭제
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* 좋아요 탭 */}
      {activeTab === "likes" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {likedCharacters.length === 0 ? (
            <div className="glass-card" style={{ borderRadius: 24, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              좋아요한 캐릭터가 없어요.
            </div>
          ) : (
            likedCharacters.map(char => (
              <div key={char.id} className="glass-card" style={{ borderRadius: 20, padding: 18, display: "flex", alignItems: "center", gap: 16 }}>
                <div
                  style={{
                    width: 52, height: 52, borderRadius: "50%",
                    background: "var(--gradient-cosmic)",
                    display: "grid", placeItems: "center",
                    fontWeight: 700, fontSize: 20, flexShrink: 0,
                  }}
                >
                  {char.name?.[0]}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700 }}>{char.name}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>{char.description}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 업적 탭 */}
      {activeTab === "achievements" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* 달성 현황 */}
          <div className="glass-card" style={{ borderRadius: 20, padding: 20 }}>
            <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>
              달성 현황
            </div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>
              {achievedList.length} <span style={{ color: "var(--text-muted)", fontSize: 14 }}>/ {achievements.length}</span>
            </div>
            <div style={{ marginTop: 10, height: 6, borderRadius: 999, background: "var(--border-default)", overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  width: `${achievements.length ? (achievedList.length / achievements.length) * 100 : 0}%`,
                  background: "var(--gradient-cosmic)",
                  borderRadius: 999,
                  transition: "width .5s ease",
                }}
              />
            </div>
          </div>

          {/* 칭호 장착 */}
          {achievedList.length > 0 && (
            <div className="glass-card" style={{ borderRadius: 20, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase" }}>
                칭호 장착
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, textAlign: "center" }}>
                {user?.equipped_prefix && <span style={{ color: "var(--primary)" }}>[{user.equipped_prefix}] </span>}
                <span>{user?.username}</span>
                {user?.equipped_suffix && <span style={{ color: "var(--primary)" }}> [{user.equipped_suffix}]</span>}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 8 }}>앞 칭호</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 150, overflowY: "auto" }}>
                    <button
                      onClick={() => handleEquipTitle("", user?.equipped_suffix ?? "")}
                      style={{
                        padding: "8px 12px", borderRadius: 10, fontSize: 13,
                        border: !user?.equipped_prefix ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                        background: !user?.equipped_prefix ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                        color: !user?.equipped_prefix ? "var(--primary)" : "var(--text-muted)",
                        cursor: "pointer",
                      }}
                    >
                      없음
                    </button>
                    {achievedList.filter(a => a.prefix_title).map(a => (
                      <button
                        key={a.code}
                        onClick={() => handleEquipTitle(a.prefix_title, user?.equipped_suffix ?? "")}
                        style={{
                          padding: "8px 12px", borderRadius: 10, fontSize: 13,
                          border: user?.equipped_prefix === a.prefix_title ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                          background: user?.equipped_prefix === a.prefix_title ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                          color: user?.equipped_prefix === a.prefix_title ? "var(--primary)" : "var(--text-muted)",
                          cursor: "pointer",
                        }}
                      >
                        [{a.prefix_title}]
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 8 }}>뒤 칭호</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 150, overflowY: "auto" }}>
                    <button
                      onClick={() => handleEquipTitle(user?.equipped_prefix ?? "", "")}
                      style={{
                        padding: "8px 12px", borderRadius: 10, fontSize: 13,
                        border: !user?.equipped_suffix ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                        background: !user?.equipped_suffix ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                        color: !user?.equipped_suffix ? "var(--primary)" : "var(--text-muted)",
                        cursor: "pointer",
                      }}
                    >
                      없음
                    </button>
                    {achievedList.filter(a => a.suffix_title).map(a => (
                      <button
                        key={a.code}
                        onClick={() => handleEquipTitle(user?.equipped_prefix ?? "", a.suffix_title)}
                        style={{
                          padding: "8px 12px", borderRadius: 10, fontSize: 13,
                          border: user?.equipped_suffix === a.suffix_title ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                          background: user?.equipped_suffix === a.suffix_title ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                          color: user?.equipped_suffix === a.suffix_title ? "var(--primary)" : "var(--text-muted)",
                          cursor: "pointer",
                        }}
                      >
                        [{a.suffix_title}]
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {equipMessage && (
                <div style={{ color: equipMessage.includes("실패") ? "#ff6b8a" : "#49d89a", fontSize: 13, textAlign: "center" }}>
                  {equipMessage}
                </div>
              )}
            </div>
          )}

          {/* 업적 목록 */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {achievements.map(a => (
              <div
                key={a.code}
                className="glass-card"
                style={{
                  borderRadius: 16, padding: 16,
                  display: "flex", alignItems: "center", gap: 14,
                  opacity: a.achieved ? 1 : 0.5,
                }}
              >
                <div
                  style={{
                    width: 44, height: 44, borderRadius: 12, flexShrink: 0,
                    background: a.achieved ? `${DIFFICULTY_COLOR[a.difficulty]}22` : "rgba(255,255,255,.04)",
                    border: `1px solid ${a.achieved ? DIFFICULTY_COLOR[a.difficulty] : "var(--border-default)"}`,
                    display: "grid", placeItems: "center",
                    fontSize: 20,
                  }}
                >
                  {a.achieved ? "✦" : "?"}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{a.title}</span>
                    <span
                      style={{
                        padding: "2px 8px", borderRadius: 999, fontSize: 11,
                        background: `${DIFFICULTY_COLOR[a.difficulty]}22`,
                        color: DIFFICULTY_COLOR[a.difficulty],
                        border: `1px solid ${DIFFICULTY_COLOR[a.difficulty]}44`,
                      }}
                    >
                      {DIFFICULTY_LABEL[a.difficulty]}
                    </span>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 3 }}>{a.description}</div>
                  {(a.prefix_title || a.suffix_title) && (
                    <div style={{ marginTop: 4, fontSize: 11, color: "var(--primary)" }}>
                      칭호: {a.prefix_title && `[${a.prefix_title}]`} {a.suffix_title && `[${a.suffix_title}]`}
                    </div>
                  )}
                </div>
                <div style={{ color: "var(--gold)", fontSize: 13, fontWeight: 600, flexShrink: 0 }}>
                  +{a.reward_token.toLocaleString()} 🥈
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 설정 탭 */}
      {activeTab === "settings" && (
        <div className="glass-card" style={{ borderRadius: 24, padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
          {/* 출력량 */}
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>기본 출력량</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}>AI 응답의 기본 길이를 설정해요.</div>
            <div style={{ display: "flex", gap: 10 }}>
              {[{ label: "짧게", value: "short" }, { label: "보통", value: "medium" }, { label: "길게", value: "long" }].map(opt => (
                <button
                  key={opt.value}
                  onClick={async () => {
                    await axios.patch(`${apiUrl}/users/me/settings`, { output_length: opt.value }, { headers });
                    setUser((prev: any) => ({ ...prev, output_length: opt.value }));
                  }}
                  style={{
                    flex: 1, padding: "12px", borderRadius: 14,
                    border: user?.output_length === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                    background: user?.output_length === opt.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                    color: user?.output_length === opt.value ? "var(--primary)" : "var(--text-muted)",
                    fontWeight: 600, cursor: "pointer",
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 세이프티 모드 */}
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>세이프티 모드</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}>부적절한 콘텐츠를 필터링해요.</div>
            <div style={{ display: "flex", gap: 10 }}>
              {[{ label: "켜기", value: 1 }, { label: "끄기", value: 0 }].map(opt => (
                <button
                  key={opt.value}
                  onClick={async () => {
                    await axios.patch(`${apiUrl}/users/me/settings`, { safety_mode: opt.value }, { headers });
                    setUser((prev: any) => ({ ...prev, safety_mode: opt.value }));
                  }}
                  style={{
                    flex: 1, padding: "12px", borderRadius: 14,
                    border: user?.safety_mode === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                    background: user?.safety_mode === opt.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                    color: user?.safety_mode === opt.value ? "var(--primary)" : "var(--text-muted)",
                    fontWeight: 600, cursor: "pointer",
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 회원 탈퇴 */}
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>회원 탈퇴</div>
            <button
              onClick={async () => {
                if (!confirm("정말 탈퇴할까요? 모든 데이터가 삭제돼요.")) return;
                await axios.delete(`${apiUrl}/users/me`, { headers });
                window.location.reload();
              }}
              style={{
                width: "100%", padding: "14px", borderRadius: 14,
                border: "1px solid rgba(255,107,138,.3)",
                background: "rgba(255,107,138,.08)",
                color: "#ff6b8a", fontWeight: 600, cursor: "pointer",
              }}
            >
              회원 탈퇴
            </button>
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
    </div>
  );
}