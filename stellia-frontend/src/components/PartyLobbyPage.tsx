import { useState, useEffect } from "react";
import axios from "axios";
import type { User } from "../App";

interface PartyLobbyPageProps {
  apiUrl: string;
  token: string;
  user: User | null;
  onBack: () => void;
  onEnterRoom: (roomCode: string) => void;
}

export default function PartyLobbyPage({ apiUrl, token, user, onBack, onEnterRoom }: PartyLobbyPageProps) {
  const [stories, setStories] = useState<any[]>([]);
  const [invitations, setInvitations] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"stories" | "invitations">("stories");
  const [joinCode, setJoinCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/party/stories`, { headers })
      .then(res => setStories(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/party/invitations/me`, { headers })
      .then(res => setInvitations(res.data))
      .catch(console.error);
  }, []);

  const handleCreateRoom = async (storyId: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(`${apiUrl}/party/rooms`, {
        story_id: storyId,
        max_members: 4,
      }, { headers });
      onEnterRoom(res.data.code);
    } catch {
      setError("방 생성에 실패했어요.");
    } finally {
      setLoading(false);
    }
  };

  const handleJoinRoom = async () => {
    if (!joinCode.trim()) return;
    setLoading(true);
    setError("");
    try {
      await axios.post(`${apiUrl}/party/rooms/join`, {
        code: joinCode.toUpperCase(),
        character_stats: { name: user?.username ?? "모험가" },
      }, { headers });
      onEnterRoom(joinCode.toUpperCase());
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "방 참가에 실패했어요.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvitation = async (invitationId: number, roomCode: string) => {
    try {
      await axios.patch(`${apiUrl}/party/invitations/${invitationId}/accept`, {}, { headers });
      onEnterRoom(roomCode);
    } catch {
      setError("초대 수락에 실패했어요.");
    }
  };

  const handleRejectInvitation = async (invitationId: number) => {
    try {
      await axios.patch(`${apiUrl}/party/invitations/${invitationId}/reject`, {}, { headers });
      setInvitations(prev => prev.filter(i => i.id !== invitationId));
    } catch {
      setError("초대 거절에 실패했어요.");
    }
  };

  const GENRE_COLOR: Record<string, string> = {
    "판타지": "var(--primary)",
    "로맨스": "#ff6b8a",
    "액션": "#ff9af3",
    "공포": "#ff6b6b",
    "SF": "var(--secondary)",
    "기타": "var(--text-muted)",
  };

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh", display: "flex", flexDirection: "column" }}>

      {/* 헤더 */}
      <div style={{
        display: "flex", alignItems: "center", gap: 16,
        padding: "24px 32px",
        background: "rgba(9,11,20,.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
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
        }}>⚔ 파티챗</div>
      </div>

      <div style={{ flex: 1, padding: "32px", maxWidth: 900, margin: "0 auto", width: "100%" }}>

        {/* 빠른 방 생성 */}
        <div className="glass-card" style={{ borderRadius: 20, padding: 20, marginBottom: 24 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>새 파티 만들기</div>
          <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>
            바로 파티방을 만들어요.
          </div>
          <button
            onClick={() => handleCreateRoom(1)}
            disabled={loading}
            style={{
              width: "100%", padding: "14px", borderRadius: 14, border: "none",
              background: "var(--gradient-cosmic)",
              color: "#fff", fontWeight: 700, fontSize: 15,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
            }}
          >⚔ 파티방 만들기</button>
          {error && <div style={{ color: "#ff6b8a", fontSize: 13, marginTop: 8 }}>{error}</div>}
        </div>

        {/* 방 코드 입력 */}
        <div className="glass-card" style={{ borderRadius: 20, padding: 20, marginBottom: 24 }}>
          <div style={{ fontWeight: 600, marginBottom: 12 }}>방 코드로 참가</div>
          <div style={{ display: "flex", gap: 10 }}>
            <input
              value={joinCode}
              onChange={e => setJoinCode(e.target.value.toUpperCase())}
              placeholder="방 코드 입력 (예: ABC123)"
              maxLength={6}
              style={{
                flex: 1, padding: "12px 16px", borderRadius: 12,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.04)",
                color: "var(--text-primary)", fontSize: 15, outline: "none",
                letterSpacing: "0.2em", fontWeight: 700,
              }}
            />
            <button
              onClick={handleJoinRoom}
              disabled={loading || !joinCode.trim()}
              style={{
                padding: "12px 24px", borderRadius: 12, border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 700, cursor: "pointer",
                opacity: loading || !joinCode.trim() ? 0.6 : 1,
              }}
            >참가</button>
          </div>
        </div>

        {/* 탭 */}
        <div style={{
          display: "flex", borderRadius: 16,
          background: "rgba(255,255,255,.04)",
          border: "1px solid var(--border-default)",
          overflow: "hidden", marginBottom: 24,
        }}>
          {[
            { id: "stories", label: "스토리 목록" },
            { id: "invitations", label: `초대 ${invitations.length > 0 ? `(${invitations.length})` : ""}` },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id as any)} style={{
              flex: 1, padding: "12px", border: "none",
              background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 14, cursor: "pointer",
            }}>{tab.label}</button>
          ))}
        </div>

        {/* 스토리 목록 */}
        {activeTab === "stories" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 20 }}>
            {stories.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: 14, padding: "40px 0" }}>등록된 스토리가 없어요.</div>
            ) : stories.map(story => (
              <div key={story.id} className="glass-card" style={{ borderRadius: 20, overflow: "hidden" }}>
                {story.image_url ? (
                  <img src={story.image_url} alt={story.title}
                    style={{ width: "100%", height: 140, objectFit: "cover" }} />
                ) : (
                  <div style={{
                    height: 140, background: "var(--gradient-cosmic)",
                    display: "grid", placeItems: "center", fontSize: 40,
                  }}>⚔</div>
                )}
                <div style={{ padding: 18 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 15 }}>{story.title}</span>
                    {story.is_official && (
                      <span style={{
                        padding: "2px 8px", borderRadius: 999, fontSize: 11,
                        background: "rgba(246,198,91,.15)", color: "var(--gold)",
                        border: "1px solid rgba(246,198,91,.3)",
                      }}>공식</span>
                    )}
                  </div>
                  <span style={{
                    padding: "3px 10px", borderRadius: 999, fontSize: 12,
                    background: "rgba(139,124,255,.12)",
                    color: GENRE_COLOR[story.genre] || "var(--primary)",
                    border: "1px solid rgba(139,124,255,.2)",
                  }}>{story.genre}</span>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 10, lineHeight: 1.6 }}>
                    {story.background?.slice(0, 60)}...
                  </div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 14 }}>
                    <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
                      추천 {story.recommended_players}인 · {story.min_players}~{story.max_players}인
                    </div>
                    <button
                      onClick={() => handleCreateRoom(story.id)}
                      disabled={loading}
                      style={{
                        padding: "8px 16px", borderRadius: 10, border: "none",
                        background: "var(--gradient-cosmic)",
                        color: "#fff", fontWeight: 600, fontSize: 13,
                        cursor: "pointer", opacity: loading ? 0.6 : 1,
                      }}
                    >방 만들기</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 초대 목록 */}
        {activeTab === "invitations" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {invitations.length === 0 ? (
              <div className="glass-card" style={{ borderRadius: 24, padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
                받은 초대가 없어요.
              </div>
            ) : invitations.map(inv => (
              <div key={inv.id} className="glass-card"
                style={{ borderRadius: 18, padding: 18, display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{inv.inviter_name}님의 초대</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
                    방 코드: {inv.room_code}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => handleAcceptInvitation(inv.id, inv.room_code)} style={{
                    padding: "8px 16px", borderRadius: 10, border: "none",
                    background: "var(--gradient-cosmic)",
                    color: "#fff", fontWeight: 600, fontSize: 13, cursor: "pointer",
                  }}>수락</button>
                  <button onClick={() => handleRejectInvitation(inv.id)} style={{
                    padding: "8px 16px", borderRadius: 10,
                    border: "1px solid rgba(255,107,138,.3)",
                    background: "rgba(255,107,138,.08)",
                    color: "#ff6b8a", fontSize: 13, cursor: "pointer",
                  }}>거절</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}