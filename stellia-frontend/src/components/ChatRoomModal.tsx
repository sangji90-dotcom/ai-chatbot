import { useState, useEffect } from "react";
import axios from "axios";

interface ChatRoomModalProps {
  apiUrl: string;
  token: string;
  characterId: string;
  sessionId: string;
  onClose: () => void;
  onExportPdf: () => void;
}

export default function ChatRoomModal({
  apiUrl, token, characterId, onClose, onExportPdf
}: ChatRoomModalProps) {
  const [activeSection, setActiveSection] = useState<"main" | "usernote" | "persona" | "memorybook" | "output">("main");
  const [user, setUser] = useState<any>(null);
  const [userNote, setUserNote] = useState("");
  const [persona, setPersona] = useState("");
  const [memoryBook, setMemoryBook] = useState<any[]>([]);
  const [newMemory, setNewMemory] = useState("");
  const [outputLength, setOutputLength] = useState("medium");
  const [imageMode, setImageMode] = useState({
    chat: true,
    background: true,
    bottom: true,
    multi: false,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/tokens/me`, { headers })
      .then(res => setUser(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/users/me`, { headers })
      .then(res => setOutputLength(res.data.output_length || "medium"))
      .catch(console.error);

    axios.get(`${apiUrl}/users/me/memory-book/${characterId}`, { headers })
      .then(res => setMemoryBook(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/users/me/notes/${characterId}`, { headers })
      .then(res => { if (res.data.length > 0) setUserNote(res.data[0].content); })
      .catch(console.error);

    axios.get(`${apiUrl}/users/me/personas/${characterId}`, { headers })
      .then(res => { if (res.data.length > 0) setPersona(res.data[0].content); })
      .catch(console.error);
  }, []);

  const handleSaveUserNote = async () => {
    setLoading(true);
    setMessage("");
    try {
      await axios.post(`${apiUrl}/users/me/notes`, {
        character_id: characterId,
        content: userNote,
      }, { headers });
      setMessage("저장됐어요.");
    } catch {
      setMessage("저장 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePersona = async () => {
    setLoading(true);
    setMessage("");
    try {
      await axios.post(`${apiUrl}/users/me/personas`, {
        character_id: characterId,
        content: persona,
        name: "",
      }, { headers });
      setMessage("저장됐어요.");
    } catch {
      setMessage("저장 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleAddMemory = async () => {
    if (!newMemory.trim()) return;
    try {
      await axios.post(`${apiUrl}/users/me/memory-book`, {
        character_id: characterId,
        content: newMemory,
        title: "",
      }, { headers });
      setNewMemory("");
      const res = await axios.get(`${apiUrl}/users/me/memory-book/${characterId}`, { headers });
      setMemoryBook(res.data);
    } catch {
      setMessage("추가 실패");
    }
  };

  const handleDeleteMemory = async (id: number) => {
    try {
      await axios.delete(`${apiUrl}/users/me/memory-book/${id}`, { headers });
      setMemoryBook(prev => prev.filter(m => m.id !== id));
    } catch {
      setMessage("삭제 실패");
    }
  };

  const handleSaveOutputLength = async (length: string) => {
    setOutputLength(length);
    await axios.patch(`${apiUrl}/users/me/settings`, { output_length: length }, { headers });
  };

  const handleExportText = async () => {
    try {
      const res = await axios.get(`${apiUrl}/chat/history/${characterId}`, { headers });
      const text = res.data
        .filter((m: any) => m.role !== "system")
        .map((m: any) => `[${m.role === "user" ? "나" : "AI"}] ${m.content}`)
        .join("\n\n");
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `대화_${characterId}.txt`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setMessage("내보내기 실패");
    }
  };

  const inputStyle = {
    padding: "12px 16px", borderRadius: 12,
    border: "1px solid var(--border-default)",
    background: "rgba(255,255,255,.04)",
    color: "var(--text-primary)", fontSize: 14,
    outline: "none", width: "100%",
    boxSizing: "border-box" as const,
  };

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.6)",
          backdropFilter: "blur(4px)",
        }}
      />
      <div
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 460, maxWidth: "92vw",
          maxHeight: "85vh",
          borderRadius: 28,
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(0,0,0,.5)",
          display: "flex", flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* 헤더 */}
        <div
          style={{
            padding: "20px 24px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: "1px solid var(--border-subtle)",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {activeSection !== "main" && (
              <button
                onClick={() => { setActiveSection("main"); setMessage(""); }}
                style={{
                  width: 32, height: 32, borderRadius: 8,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-muted)", cursor: "pointer", fontSize: 14,
                }}
              >
                ←
              </button>
            )}
            <div style={{ fontWeight: 700, fontSize: 16 }}>
              {activeSection === "main" && "채팅방 관리"}
              {activeSection === "usernote" && "유저노트"}
              {activeSection === "persona" && "페르소나"}
              {activeSection === "memorybook" && "메모리북"}
              {activeSection === "output" && "출력량 설정"}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              width: 32, height: 32, borderRadius: 8,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", cursor: "pointer", fontSize: 16,
            }}
          >
            ×
          </button>
        </div>

        <div style={{ overflowY: "auto", flex: 1, padding: 20 }}>

          {/* 메인 */}
          {activeSection === "main" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {/* 럭키코인 */}
              <div
                style={{
                  borderRadius: 18, padding: 18,
                  background: "linear-gradient(135deg, rgba(246,198,91,.1), rgba(246,198,91,.05))",
                  border: "1px solid rgba(246,198,91,.2)",
                }}
              >
                <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 12 }}>내 럭키코인</div>
                <div style={{ display: "flex", gap: 20 }}>
                  <div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>🥇 금화</div>
                    <div style={{ fontWeight: 700, color: "var(--gold)" }}>{user?.token_purchased?.toLocaleString() ?? 0}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>🥈 은화</div>
                    <div style={{ fontWeight: 700, color: "#c8c8dc" }}>{user?.token_event?.toLocaleString() ?? 0}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>합계</div>
                    <div style={{ fontWeight: 700, color: "var(--gold)" }}>✦ {user?.token_balance?.toLocaleString() ?? 0}</div>
                  </div>
                </div>
              </div>

              {/* 이미지 ON/OFF */}
              <div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".1em", marginBottom: 12 }}>이미지 ON/OFF</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { key: "chat", label: "채팅 이미지", icon: "🖼" },
                    { key: "background", label: "배경 이미지", icon: "🌌" },
                    { key: "bottom", label: "하단 이미지", icon: "📸" },
                    { key: "multi", label: "멀티 이미지", icon: "🎞" },
                  ].map(item => (
                    <button
                      key={item.key}
                      onClick={() => setImageMode(prev => ({ ...prev, [item.key]: !prev[item.key as keyof typeof prev] }))}
                      style={{
                        padding: "14px 12px", borderRadius: 14,
                        border: imageMode[item.key as keyof typeof imageMode]
                          ? "1px solid var(--primary)"
                          : "1px solid var(--border-default)",
                        background: imageMode[item.key as keyof typeof imageMode]
                          ? "rgba(139,124,255,.12)"
                          : "rgba(255,255,255,.02)",
                        color: imageMode[item.key as keyof typeof imageMode]
                          ? "var(--primary)"
                          : "var(--text-muted)",
                        cursor: "pointer", fontSize: 13, fontWeight: 600,
                        display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                      }}
                    >
                      <span style={{ fontSize: 24 }}>{item.icon}</span>
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 채팅방 설정 */}
              <div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".1em", marginBottom: 12 }}>채팅방 설정</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { id: "usernote", label: "유저노트", icon: "📝" },
                    { id: "persona", label: "페르소나", icon: "🎭" },
                    { id: "memorybook", label: "메모리북", icon: "📖" },
                    { id: "output", label: "출력량 설정", icon: "⚡" },
                  ].map(item => (
                    <button
                      key={item.id}
                      onClick={() => setActiveSection(item.id as any)}
                      style={{
                        padding: "14px 12px", borderRadius: 14,
                        border: "1px solid var(--border-default)",
                        background: "rgba(255,255,255,.02)",
                        color: "var(--text-secondary)",
                        cursor: "pointer", fontSize: 13, fontWeight: 600,
                        display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                      }}
                    >
                      <span style={{ fontSize: 24 }}>{item.icon}</span>
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 대화 저장 */}
              <div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, letterSpacing: ".1em", marginBottom: 12 }}>대화 저장</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <button
                    onClick={() => { onExportPdf(); onClose(); }}
                    style={{
                      padding: "14px 12px", borderRadius: 14,
                      border: "1px solid var(--border-default)",
                      background: "rgba(255,255,255,.02)",
                      color: "var(--text-secondary)",
                      cursor: "pointer", fontSize: 13, fontWeight: 600,
                      display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                    }}
                  >
                    <span style={{ fontSize: 24 }}>📄</span>
                    PDF
                  </button>
                  <button
                    onClick={handleExportText}
                    style={{
                      padding: "14px 12px", borderRadius: 14,
                      border: "1px solid var(--border-default)",
                      background: "rgba(255,255,255,.02)",
                      color: "var(--text-secondary)",
                      cursor: "pointer", fontSize: 13, fontWeight: 600,
                      display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                    }}
                  >
                    <span style={{ fontSize: 24 }}>📝</span>
                    텍스트
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 유저노트 */}
          {activeSection === "usernote" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6 }}>
                AI가 알아야 할 나에 대한 정보를 입력해줘요.<br />
                예: 이름, 직업, 관계 설정 등
              </div>
              <textarea
                value={userNote}
                onChange={e => setUserNote(e.target.value)}
                placeholder="예: 내 이름은 민준이고, 이 캐릭터와 친구 사이야."
                style={{ ...inputStyle, minHeight: 160, resize: "vertical" as const }}
              />
              {message && (
                <div style={{ color: message.includes("실패") ? "#ff6b8a" : "#49d89a", fontSize: 13 }}>
                  {message}
                </div>
              )}
              <button
                onClick={handleSaveUserNote}
                disabled={loading}
                style={{
                  padding: "14px", borderRadius: 14, border: "none",
                  background: "var(--gradient-cosmic)",
                  color: "#fff", fontWeight: 700, cursor: "pointer",
                  opacity: loading ? 0.7 : 1,
                }}
              >
                {loading ? "저장 중..." : "저장"}
              </button>
            </div>
          )}

          {/* 페르소나 */}
          {activeSection === "persona" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6 }}>
                대화 속 내 캐릭터를 설정해요.<br />
                예: 나는 기사단의 단장이고, 이 캐릭터는 내 부하야.
              </div>
              <textarea
                value={persona}
                onChange={e => setPersona(e.target.value)}
                placeholder="예: 나는 마법사 길드의 마스터야. 이 캐릭터는 내 제자."
                style={{ ...inputStyle, minHeight: 160, resize: "vertical" as const }}
              />
              {message && (
                <div style={{ color: message.includes("실패") ? "#ff6b8a" : "#49d89a", fontSize: 13 }}>
                  {message}
                </div>
              )}
              <button
                onClick={handleSavePersona}
                disabled={loading}
                style={{
                  padding: "14px", borderRadius: 14, border: "none",
                  background: "var(--gradient-cosmic)",
                  color: "#fff", fontWeight: 700, cursor: "pointer",
                  opacity: loading ? 0.7 : 1,
                }}
              >
                {loading ? "저장 중..." : "저장"}
              </button>
            </div>
          )}

          {/* 메모리북 */}
          {activeSection === "memorybook" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6 }}>
                AI가 반드시 기억해야 할 중요한 내용을 저장해요.
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={newMemory}
                  onChange={e => setNewMemory(e.target.value)}
                  placeholder="기억할 내용 입력"
                  style={{ ...inputStyle, flex: 1 }}
                  onKeyDown={e => e.key === "Enter" && handleAddMemory()}
                />
                <button
                  onClick={handleAddMemory}
                  style={{
                    padding: "12px 16px", borderRadius: 12, border: "none",
                    background: "var(--gradient-cosmic)",
                    color: "#fff", fontWeight: 600, cursor: "pointer",
                  }}
                >
                  추가
                </button>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {memoryBook.length === 0 ? (
                  <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "20px 0" }}>
                    저장된 기억이 없어요.
                  </div>
                ) : (
                  memoryBook.map((m, i) => (
                    <div
                      key={m.id}
                      style={{
                        display: "flex", alignItems: "center", gap: 12,
                        padding: "12px 14px", borderRadius: 12,
                        background: "rgba(255,255,255,.03)",
                        border: "1px solid var(--border-subtle)",
                      }}
                    >
                      <span style={{ color: "var(--text-muted)", fontSize: 12, flexShrink: 0 }}>{i + 1}</span>
                      <div style={{ flex: 1, fontSize: 14, lineHeight: 1.5 }}>{m.content}</div>
                      <button
                        onClick={() => handleDeleteMemory(m.id)}
                        style={{
                          background: "none", border: "none",
                          color: "#ff6b8a", cursor: "pointer", fontSize: 16, flexShrink: 0,
                        }}
                      >
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
              {message && (
                <div style={{ color: "#ff6b8a", fontSize: 13 }}>{message}</div>
              )}
            </div>
          )}

          {/* 출력량 설정 */}
          {activeSection === "output" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6 }}>
                AI 응답의 길이를 설정해요.
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { value: "short", label: "짧게", desc: "간결하고 빠른 응답", tokens: "300토큰/회" },
                  { value: "medium", label: "보통", desc: "적당한 길이의 응답", tokens: "1,000토큰/회" },
                  { value: "long", label: "길게", desc: "상세하고 풍부한 응답", tokens: "2,000토큰/회" },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => handleSaveOutputLength(opt.value)}
                    style={{
                      padding: "16px", borderRadius: 14, textAlign: "left",
                      border: outputLength === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: outputLength === opt.value ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: outputLength === opt.value ? "var(--primary)" : "var(--text-muted)",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ fontWeight: 700, marginBottom: 4 }}>{opt.label}</div>
                    <div style={{ fontSize: 12 }}>{opt.desc}</div>
                    <div style={{ fontSize: 11, color: "var(--gold)", marginTop: 4 }}>✦ {opt.tokens}</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}