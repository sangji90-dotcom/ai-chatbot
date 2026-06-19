import { useState, useEffect } from "react";
import axios from "axios";

interface AdminPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
}

export default function AdminPage({ apiUrl, token, onBack }: AdminPageProps) {
  const headers = { Authorization: `Bearer ${token}` };
  const [activeTab, setActiveTab] = useState<"stats" | "users" | "reports" | "inquiries" | "tokens">("stats");
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [inquiries, setInquiries] = useState<any[]>([]);
  const [searchQ, setSearchQ] = useState("");
  const [msg, setMsg] = useState("");
  const [grantModal, setGrantModal] = useState<{userId: number, username: string} | null>(null);
  const [grantAmount, setGrantAmount] = useState("");
  const [grantReason, setGrantReason] = useState("");
  const [answerModal, setAnswerModal] = useState<any | null>(null);
  const [answerText, setAnswerText] = useState("");

  const showMsg = (m: string) => { setMsg(m); setTimeout(() => setMsg(""), 3000); };

  useEffect(() => {
    axios.get(`${apiUrl}/admin/stats`, { headers }).then(r => setStats(r.data)).catch(console.error);
  }, []);

  useEffect(() => {
    if (activeTab === "users") fetchUsers();
    if (activeTab === "reports") fetchReports();
    if (activeTab === "inquiries") fetchInquiries();
  }, [activeTab]);

  const fetchUsers = (q?: string) => {
    const url = q ? `${apiUrl}/admin/users?q=${q}` : `${apiUrl}/admin/users`;
    axios.get(url, { headers }).then(r => setUsers(r.data)).catch(console.error);
  };

  const fetchReports = () => {
    axios.get(`${apiUrl}/admin/reports`, { headers }).then(r => setReports(r.data)).catch(console.error);
  };

  const fetchInquiries = () => {
    axios.get(`${apiUrl}/admin/inquiries`, { headers }).then(r => setInquiries(r.data)).catch(console.error);
  };

  const handleSuspend = async (userId: number, suspended: number) => {
    const url = `${apiUrl}/admin/users/${userId}/${suspended ? "unsuspend" : "suspend"}`;
    await axios.patch(url, {}, { headers });
    showMsg(suspended ? "정지 해제 완료" : "정지 완료");
    fetchUsers(searchQ || undefined);
  };

  const handleGrantAdmin = async (userId: number, isAdmin: number) => {
    const url = `${apiUrl}/admin/users/${userId}/${isAdmin ? "revoke-admin" : "grant-admin"}`;
    await axios.patch(url, {}, { headers });
    showMsg(isAdmin ? "관리자 해제 완료" : "관리자 부여 완료");
    fetchUsers(searchQ || undefined);
  };

  const handleGrantToken = async () => {
    if (!grantModal || !grantAmount || !grantReason) return;
    try {
      await axios.post(`${apiUrl}/admin/users/${grantModal.userId}/grant-token`,
        { amount: Number(grantAmount), reason: grantReason }, { headers });
      showMsg(`${grantAmount}토큰 지급 완료`);
      setGrantModal(null); setGrantAmount(""); setGrantReason("");
    } catch (e: any) {
      showMsg(e.response?.data?.detail ?? "오류 발생");
    }
  };

  const handleDismissReport = async (id: number) => {
    await axios.patch(`${apiUrl}/admin/reports/${id}/dismiss`, {}, { headers });
    showMsg("신고 무시 완료");
    fetchReports();
  };

  const handleActionReport = async (id: number) => {
    if (!confirm("캐릭터를 삭제할까요?")) return;
    await axios.patch(`${apiUrl}/admin/reports/${id}/action`, {}, { headers });
    showMsg("신고 처리 완료 (캐릭터 삭제)");
    fetchReports();
  };

  const handleAnswer = async () => {
    if (!answerModal || !answerText) return;
    await axios.patch(`${apiUrl}/admin/inquiries/${answerModal.id}/answer`,
      { answer: answerText }, { headers });
    showMsg("답변 완료");
    setAnswerModal(null); setAnswerText("");
    fetchInquiries();
  };

  const tabs = [
    { id: "stats", label: "📊 통계" },
    { id: "users", label: "👥 유저" },
    { id: "reports", label: "🚨 신고" },
    { id: "inquiries", label: "💬 문의" },
  ] as const;

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh" }}>

      {/* 네비바 */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 10,
        display: "flex", alignItems: "center", gap: 16,
        padding: "16px 32px",
        background: "rgba(9,11,20,.95)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 22, cursor: "pointer" }}>←</button>
        <span style={{
          fontSize: 20, fontWeight: 700,
          background: "linear-gradient(90deg, #ff6b8a, #ff9532)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
        }}>관리자 패널</span>
      </nav>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px" }}>

        {/* 토스트 */}
        {msg && (
          <div style={{
            padding: "12px 20px", borderRadius: 12, marginBottom: 16,
            background: "rgba(73,216,154,.15)", border: "1px solid rgba(73,216,154,.3)",
            color: "#49d89a", fontSize: 14, textAlign: "center",
          }}>{msg}</div>
        )}

        {/* 탭 */}
        <div style={{
          display: "flex", borderRadius: 16,
          background: "rgba(255,255,255,.04)",
          border: "1px solid var(--border-default)",
          overflow: "hidden", marginBottom: 24,
        }}>
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              flex: 1, padding: "12px", border: "none",
              background: activeTab === tab.id ? "linear-gradient(90deg,#ff6b8a,#ff9532)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 13, cursor: "pointer",
            }}>{tab.label}</button>
          ))}
        </div>

        {/* 통계 탭 */}
        {activeTab === "stats" && stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            {[
              { label: "전체 유저", value: stats.user_count, color: "#8b7cff" },
              { label: "전체 캐릭터", value: stats.character_count, color: "#5fd6ff" },
              { label: "전체 대화", value: stats.chat_count, color: "#49d89a" },
              { label: "미처리 신고", value: stats.pending_reports, color: "#ff6b8a" },
              { label: "미처리 문의", value: stats.pending_inquiries, color: "#ffc850" },
            ].map(s => (
              <div key={s.label} style={{
                borderRadius: 20, padding: "24px",
                border: "1px solid var(--border-default)",
                background: "rgba(17,21,40,.7)",
                textAlign: "center",
              }}>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 10 }}>{s.label}</div>
                <div style={{ fontSize: 32, fontWeight: 700, color: s.color }}>{s.value?.toLocaleString()}</div>
              </div>
            ))}
          </div>
        )}

        {/* 유저 탭 */}
        {activeTab === "users" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", gap: 10 }}>
              <input
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                onKeyDown={e => e.key === "Enter" && fetchUsers(searchQ)}
                placeholder="이메일 / 닉네임 검색..."
                style={{
                  flex: 1, padding: "12px 16px", borderRadius: 12,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-primary)", outline: "none",
                }}
              />
              <button onClick={() => fetchUsers(searchQ)} style={{
                padding: "12px 20px", borderRadius: 12,
                border: "none", background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 600, cursor: "pointer",
              }}>검색</button>
            </div>

            {users.map(u => (
              <div key={u.id} style={{
                borderRadius: 16, padding: "16px 20px",
                border: "1px solid var(--border-default)",
                background: "rgba(17,21,40,.7)",
                display: "flex", alignItems: "center", gap: 14,
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 700 }}>{u.username}</span>
                    {u.is_admin === 1 && <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: "rgba(255,107,138,.15)", color: "#ff6b8a", border: "1px solid rgba(255,107,138,.3)" }}>관리자</span>}
                    {u.suspended === 1 && <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: "rgba(255,150,50,.15)", color: "#ff9532", border: "1px solid rgba(255,150,50,.3)" }}>정지</span>}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 3 }}>{u.email} · 토큰 {u.token_balance?.toLocaleString()}</div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => setGrantModal({ userId: u.id, username: u.username })} style={{
                    padding: "7px 12px", borderRadius: 10, fontSize: 12,
                    border: "1px solid rgba(73,216,154,.3)",
                    background: "rgba(73,216,154,.08)",
                    color: "#49d89a", cursor: "pointer",
                  }}>토큰 지급</button>
                  <button onClick={() => handleGrantAdmin(u.id, u.is_admin)} style={{
                    padding: "7px 12px", borderRadius: 10, fontSize: 12,
                    border: "1px solid rgba(139,124,255,.3)",
                    background: "rgba(139,124,255,.08)",
                    color: "var(--primary)", cursor: "pointer",
                  }}>{u.is_admin ? "관리자 해제" : "관리자 부여"}</button>
                  <button onClick={() => handleSuspend(u.id, u.suspended)} style={{
                    padding: "7px 12px", borderRadius: 10, fontSize: 12,
                    border: "1px solid rgba(255,107,138,.3)",
                    background: "rgba(255,107,138,.08)",
                    color: "#ff6b8a", cursor: "pointer",
                  }}>{u.suspended ? "정지 해제" : "정지"}</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 신고 탭 */}
        {activeTab === "reports" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {reports.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>미처리 신고가 없어요.</div>
            ) : reports.map(r => (
              <div key={r.id} style={{
                borderRadius: 16, padding: "16px 20px",
                border: "1px solid var(--border-default)",
                background: "rgba(17,21,40,.7)",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontWeight: 700 }}>캐릭터: {r.character_name}</span>
                  <span style={{ color: "var(--text-muted)", fontSize: 12 }}>{new Date(r.created_at).toLocaleDateString("ko-KR")}</span>
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12 }}>
                  신고자: {r.reporter_name} · 사유: {r.reason}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => handleDismissReport(r.id)} style={{
                    padding: "8px 16px", borderRadius: 10, fontSize: 13,
                    border: "1px solid var(--border-default)",
                    background: "rgba(255,255,255,.04)",
                    color: "var(--text-muted)", cursor: "pointer",
                  }}>무시</button>
                  <button onClick={() => handleActionReport(r.id)} style={{
                    padding: "8px 16px", borderRadius: 10, fontSize: 13,
                    border: "1px solid rgba(255,107,138,.3)",
                    background: "rgba(255,107,138,.08)",
                    color: "#ff6b8a", cursor: "pointer",
                  }}>캐릭터 삭제</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 문의 탭 */}
        {activeTab === "inquiries" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {inquiries.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>미처리 문의가 없어요.</div>
            ) : inquiries.map(i => (
              <div key={i.id} style={{
                borderRadius: 16, padding: "16px 20px",
                border: "1px solid var(--border-default)",
                background: "rgba(17,21,40,.7)",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontWeight: 700 }}>{i.title}</span>
                  <span style={{ color: "var(--text-muted)", fontSize: 12 }}>{i.username} · {new Date(i.created_at).toLocaleDateString("ko-KR")}</span>
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12 }}>{i.content}</div>
                <button onClick={() => { setAnswerModal(i); setAnswerText(""); }} style={{
                  padding: "8px 16px", borderRadius: 10, fontSize: 13,
                  border: "1px solid rgba(139,124,255,.3)",
                  background: "rgba(139,124,255,.08)",
                  color: "var(--primary)", cursor: "pointer",
                }}>답변하기</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 토큰 지급 모달 */}
      {grantModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.7)", display: "grid", placeItems: "center", zIndex: 100 }}>
          <div style={{ borderRadius: 24, padding: 32, background: "rgba(17,21,40,.98)", border: "1px solid var(--border-default)", width: 360 }}>
            <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 20 }}>{grantModal.username}에게 토큰 지급</div>
            <input value={grantAmount} onChange={e => setGrantAmount(e.target.value)} placeholder="수량" type="number"
              style={{ width: "100%", padding: "12px 16px", borderRadius: 12, border: "1px solid var(--border-default)", background: "rgba(255,255,255,.04)", color: "var(--text-primary)", outline: "none", marginBottom: 12, boxSizing: "border-box" as const }} />
            <input value={grantReason} onChange={e => setGrantReason(e.target.value)} placeholder="지급 사유"
              style={{ width: "100%", padding: "12px 16px", borderRadius: 12, border: "1px solid var(--border-default)", background: "rgba(255,255,255,.04)", color: "var(--text-primary)", outline: "none", marginBottom: 20, boxSizing: "border-box" as const }} />
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setGrantModal(null)} style={{ flex: 1, padding: "12px", borderRadius: 12, border: "1px solid var(--border-default)", background: "none", color: "var(--text-muted)", cursor: "pointer" }}>취소</button>
              <button onClick={handleGrantToken} style={{ flex: 1, padding: "12px", borderRadius: 12, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>지급</button>
            </div>
          </div>
        </div>
      )}

      {/* 문의 답변 모달 */}
      {answerModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.7)", display: "grid", placeItems: "center", zIndex: 100 }}>
          <div style={{ borderRadius: 24, padding: 32, background: "rgba(17,21,40,.98)", border: "1px solid var(--border-default)", width: 480 }}>
            <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>{answerModal.title}</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 20 }}>{answerModal.content}</div>
            <textarea value={answerText} onChange={e => setAnswerText(e.target.value)} placeholder="답변 내용..."
              style={{ width: "100%", padding: "12px 16px", borderRadius: 12, border: "1px solid var(--border-default)", background: "rgba(255,255,255,.04)", color: "var(--text-primary)", outline: "none", marginBottom: 20, minHeight: 120, resize: "vertical", boxSizing: "border-box" as const }} />
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setAnswerModal(null)} style={{ flex: 1, padding: "12px", borderRadius: 12, border: "1px solid var(--border-default)", background: "none", color: "var(--text-muted)", cursor: "pointer" }}>취소</button>
              <button onClick={handleAnswer} style={{ flex: 1, padding: "12px", borderRadius: 12, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>답변 전송</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}