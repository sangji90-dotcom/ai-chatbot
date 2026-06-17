import { useState, useEffect } from "react";
import axios from "axios";
import type { User } from "../App";

interface PartyRoomPageProps {
  apiUrl: string;
  token: string;
  user: User | null;
  roomCode: string;
  onBack: () => void;
  onStartChat: (roomCode: string) => void;
}

export default function PartyRoomPage({ apiUrl, token, user, roomCode, onBack, onStartChat }: PartyRoomPageProps) {
  const [room, setRoom] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [story, setStory] = useState<any>(null);
  const [outputMultiplier, setOutputMultiplier] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchRoomInfo();
    const interval = setInterval(fetchRoomInfo, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchRoomInfo = async () => {
  try {
    const res = await axios.get(`${apiUrl}/party/rooms/${roomCode}`, { headers });
    setRoom(res.data.room);
    setMembers(res.data.members);

    if (res.data.room.story_id) {
      const storyRes = await axios.get(`${apiUrl}/party/stories`, { headers });
      const found = storyRes.data.find((s: any) => s.id === res.data.room.story_id);
      if (found) setStory(found);
    }
     } catch (e) {
    console.error(e);
        }
    };

  const isHost = room?.host_id === user?.id;

  const handleUpdateSettings = async () => {
    try {
      await axios.patch(`${apiUrl}/party/rooms/${roomCode}/settings`, {
        output_multiplier: outputMultiplier,
      }, { headers });
    } catch {
      setError("설정 변경에 실패했어요.");
    }
  };

  const handleStart = async () => {
    if (members.length < 2) {
      setError("최소 2명이 필요해요.");
      return;
    }
    onStartChat(roomCode);
  };

  const handleLeave = async () => {
    try {
      await axios.delete(`${apiUrl}/party/rooms/${roomCode}/leave`, { headers });
      onBack();
    } catch {
      setError("방 나가기에 실패했어요.");
    }
  };

  const handleDelegate = async (userId: number) => {
    try {
      await axios.patch(`${apiUrl}/party/rooms/${roomCode}/delegate/${userId}`, {}, { headers });
      fetchRoomInfo();
    } catch {
      setError("방장 위임에 실패했어요.");
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(roomCode);
  };

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* 헤더 */}
      <div
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "20px 32px",
          background: "rgba(9,11,20,.85)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button
            onClick={handleLeave}
            style={{
              width: 40, height: 40, borderRadius: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
            }}
          >
            ←
          </button>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{story?.title ?? "대기실"}</div>
            <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2 }}>
              {members.length}/{room?.max_members ?? 4}명 참가 중
            </div>
          </div>
        </div>

        {/* 방 코드 */}
        <div
          onClick={handleCopyCode}
          style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "10px 18px", borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            cursor: "pointer",
          }}
        >
          <span style={{ color: "var(--text-muted)", fontSize: 13 }}>방 코드</span>
          <span style={{ fontWeight: 700, letterSpacing: "0.2em", color: "var(--primary)" }}>
            {roomCode}
          </span>
          <span style={{ color: "var(--text-muted)", fontSize: 12 }}>📋</span>
        </div>
      </div>

      <div style={{ flex: 1, padding: "32px", maxWidth: 700, margin: "0 auto", width: "100%", display: "flex", flexDirection: "column", gap: 20 }}>

        {error && (
          <div style={{ color: "#ff6b8a", fontSize: 13, textAlign: "center" }}>{error}</div>
        )}

        {/* 스토리 정보 */}
        {story && (
          <div className="glass-card" style={{ borderRadius: 20, padding: 20 }}>
            <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 12 }}>
              스토리
            </div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>{story.title}</div>
            <div style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.6 }}>
              {story.background}
            </div>
          </div>
        )}

        {/* 멤버 목록 */}
        <div className="glass-card" style={{ borderRadius: 20, padding: 20 }}>
          <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 16 }}>
            참가 멤버
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {members.map(member => (
              <div
                key={member.id}
                style={{
                  display: "flex", alignItems: "center", gap: 14,
                  padding: "12px 16px", borderRadius: 14,
                  background: "rgba(255,255,255,.03)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div
                  style={{
                    width: 42, height: 42, borderRadius: "50%",
                    background: "var(--gradient-cosmic)",
                    display: "grid", placeItems: "center",
                    fontWeight: 700, fontSize: 16,
                  }}
                >
                  {member.username?.[0]?.toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 600 }}>{member.username}</span>
                    {room?.host_id === member.user_id && (
                      <span style={{
                        padding: "2px 8px", borderRadius: 999, fontSize: 11,
                        background: "rgba(246,198,91,.15)", color: "var(--gold)",
                        border: "1px solid rgba(246,198,91,.3)",
                      }}>방장</span>
                    )}
                    {member.user_id === user?.id && (
                      <span style={{
                        padding: "2px 8px", borderRadius: 999, fontSize: 11,
                        background: "rgba(139,124,255,.15)", color: "var(--primary)",
                        border: "1px solid rgba(139,124,255,.3)",
                      }}>나</span>
                    )}
                  </div>
                </div>

                {/* 방장 위임 버튼 */}
                {isHost && member.user_id !== user?.id && (
                  <button
                    onClick={() => handleDelegate(member.user_id)}
                    style={{
                      padding: "6px 12px", borderRadius: 8, fontSize: 12,
                      border: "1px solid rgba(246,198,91,.3)",
                      background: "rgba(246,198,91,.08)",
                      color: "var(--gold)", cursor: "pointer",
                    }}
                  >
                    방장 위임
                  </button>
                )}
              </div>
            ))}

            {/* 빈 슬롯 */}
            {Array.from({ length: (room?.max_members ?? 4) - members.length }).map((_, i) => (
              <div
                key={`empty-${i}`}
                style={{
                  padding: "12px 16px", borderRadius: 14,
                  border: "1px dashed var(--border-subtle)",
                  color: "var(--text-muted)", fontSize: 14,
                  textAlign: "center",
                }}
              >
                대기 중...
              </div>
            ))}
          </div>
        </div>

        {/* 방장 설정 */}
        {isHost && (
          <div className="glass-card" style={{ borderRadius: 20, padding: 20 }}>
            <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 16 }}>
              방장 설정
            </div>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>AI 출력량 배율</div>
              <div style={{ display: "flex", gap: 10 }}>
                {[
                  { label: "기본", value: 1.0 },
                  { label: "1.5배", value: 1.5 },
                  { label: "2배", value: 2.0 },
                  { label: "3배", value: 3.0 },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setOutputMultiplier(opt.value)}
                    style={{
                      flex: 1, padding: "10px", borderRadius: 12,
                      border: outputMultiplier === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: outputMultiplier === opt.value ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                      color: outputMultiplier === opt.value ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, fontSize: 13, cursor: "pointer",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              <button
                onClick={handleUpdateSettings}
                style={{
                  marginTop: 12, width: "100%", padding: "12px", borderRadius: 12,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-secondary)", cursor: "pointer", fontWeight: 600,
                }}
              >
                설정 적용
              </button>
            </div>
          </div>
        )}

        {/* 시작 버튼 */}
        {isHost && (
          <button
            onClick={handleStart}
            disabled={loading || members.length < 2}
            style={{
              padding: "18px", borderRadius: 16, border: "none",
              background: members.length >= 2 ? "var(--gradient-cosmic)" : "rgba(255,255,255,.06)",
              color: members.length >= 2 ? "#fff" : "var(--text-muted)",
              fontWeight: 700, fontSize: 18,
              cursor: members.length >= 2 ? "pointer" : "not-allowed",
              boxShadow: members.length >= 2 ? "0 0 30px rgba(139,124,255,.3)" : "none",
            }}
          >
            {members.length < 2 ? "최소 2명 필요" : "⚔ 파티챗 시작"}
          </button>
        )}

        {!isHost && (
          <div
            style={{
              padding: "18px", borderRadius: 16,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.03)",
              color: "var(--text-muted)", fontSize: 15,
              textAlign: "center",
            }}
          >
            방장이 시작하기를 기다리는 중...
          </div>
        )}
      </div>
    </div>
  );
}