import { useState, useEffect } from "react";
import axios from "axios";

interface NoticePageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
}

export default function NoticePage({ apiUrl, token, onBack }: NoticePageProps) {
  const [notices, setNotices] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedNotice, setSelectedNotice] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    axios.get(`${apiUrl}/notices`, { headers })
      .then(res => {
        setNotices(res.data.notices);
        setTotal(res.data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh" }}>

      <nav style={{
        position: "sticky", top: 0, zIndex: 10,
        display: "flex", alignItems: "center", gap: 16,
        padding: "16px 32px",
        background: "rgba(9,11,20,.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <button onClick={selectedNotice ? () => setSelectedNotice(null) : onBack}
          style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 22, cursor: "pointer" }}>←</button>
        <span style={{ fontWeight: 700, fontSize: 18 }}>
          {selectedNotice ? selectedNotice.title : "📢 공지사항"}
        </span>
      </nav>

      <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px" }}>

        {/* 공지 목록 */}
        {!selectedNotice && (
          <>
            {loading ? (
              <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>불러오는 중...</div>
            ) : notices.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 40 }}>공지사항이 없어요.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {notices.map(notice => (
                  <div key={notice.id} onClick={() => setSelectedNotice(notice)} style={{
                    borderRadius: 16, padding: "18px 20px",
                    border: `1px solid ${notice.is_pinned ? "rgba(255,200,80,.3)" : "var(--border-default)"}`,
                    background: notice.is_pinned ? "rgba(255,200,80,.05)" : "rgba(17,21,40,.7)",
                    cursor: "pointer", transition: "all .2s ease",
                    display: "flex", alignItems: "center", gap: 12,
                  }}>
                    {notice.is_pinned && (
                      <span style={{
                        padding: "2px 8px", borderRadius: 999, fontSize: 11,
                        background: "rgba(255,200,80,.2)", color: "#ffc850",
                        border: "1px solid rgba(255,200,80,.3)", flexShrink: 0,
                      }}>📌 고정</span>
                    )}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 15 }}>{notice.title}</div>
                      <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                        {new Date(notice.created_at).toLocaleDateString("ko-KR")}
                      </div>
                    </div>
                    <span style={{ color: "var(--text-muted)", fontSize: 18 }}>›</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* 공지 상세 */}
        {selectedNotice && (
          <div style={{
            borderRadius: 20, padding: 28,
            border: "1px solid var(--border-default)",
            background: "rgba(17,21,40,.7)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              {selectedNotice.is_pinned && (
                <span style={{
                  padding: "2px 8px", borderRadius: 999, fontSize: 11,
                  background: "rgba(255,200,80,.2)", color: "#ffc850",
                  border: "1px solid rgba(255,200,80,.3)",
                }}>📌 고정</span>
              )}
              <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
                {new Date(selectedNotice.created_at).toLocaleDateString("ko-KR")}
              </span>
            </div>
            <div style={{ fontWeight: 700, fontSize: 20, marginBottom: 20 }}>{selectedNotice.title}</div>
            <div style={{
              color: "var(--text-secondary)", fontSize: 15, lineHeight: 1.9,
              whiteSpace: "pre-wrap",
            }}>{selectedNotice.content}</div>
          </div>
        )}
      </div>
    </div>
  );
}