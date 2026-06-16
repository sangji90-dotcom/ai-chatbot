import { useState, useEffect } from "react";
import axios from "axios";

interface NotificationModalProps {
  apiUrl: string;
  token: string;
  onClose: () => void;
}

export default function NotificationModal({ apiUrl, token, onClose }: NotificationModalProps) {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/notifications`, { headers })
      .then(res => setNotifications(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleReadAll = async () => {
    try {
      await axios.patch(`${apiUrl}/notifications/read-all`, {}, { headers });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: 1 })));
    } catch {
      console.error("알림 읽음 처리 실패");
    }
  };

  const handleRead = async (id: number) => {
    try {
      await axios.patch(`${apiUrl}/notifications/${id}/read`, {}, { headers });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: 1 } : n));
    } catch {
      console.error("알림 읽음 처리 실패");
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const TYPE_ICON: Record<string, string> = {
    new_character: "✨",
    token_low: "⚠️",
    token_empty: "🪙",
    achievement: "🏆",
    follow: "👤",
    default: "🔔",
  };

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.4)",
        }}
      />
      <div
        style={{
          position: "fixed",
          top: 70, right: 20,
          zIndex: 51,
          width: 380,
          maxWidth: "90vw",
          maxHeight: "70vh",
          borderRadius: 24,
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 40px rgba(0,0,0,.4)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* 헤더 */}
        <div
          style={{
            padding: "18px 20px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 16 }}>
            알림 {unreadCount > 0 && (
              <span
                style={{
                  marginLeft: 8, padding: "2px 8px", borderRadius: 999,
                  background: "var(--primary)", color: "#fff", fontSize: 12,
                }}
              >
                {unreadCount}
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            {unreadCount > 0 && (
              <button
                onClick={handleReadAll}
                style={{
                  padding: "6px 12px", borderRadius: 10, fontSize: 12,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-muted)", cursor: "pointer",
                }}
              >
                전체 읽음
              </button>
            )}
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
        </div>

        {/* 알림 목록 */}
        <div style={{ overflowY: "auto", flex: 1 }}>
          {loading ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px 0" }}>
              불러오는 중...
            </div>
          ) : notifications.length === 0 ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px 0" }}>
              알림이 없어요.
            </div>
          ) : (
            notifications.map(n => (
              <div
                key={n.id}
                onClick={() => handleRead(n.id)}
                style={{
                  padding: "14px 20px",
                  display: "flex", gap: 12, alignItems: "flex-start",
                  borderBottom: "1px solid var(--border-subtle)",
                  background: n.is_read ? "transparent" : "rgba(139,124,255,.06)",
                  cursor: "pointer",
                  transition: "background .2s ease",
                }}
              >
                <div
                  style={{
                    width: 38, height: 38, borderRadius: 12, flexShrink: 0,
                    background: "rgba(139,124,255,.12)",
                    display: "grid", placeItems: "center", fontSize: 18,
                  }}
                >
                  {TYPE_ICON[n.type] ?? TYPE_ICON.default}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: n.is_read ? 400 : 700, fontSize: 14 }}>{n.title}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 3, lineHeight: 1.5 }}>
                    {n.message}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 4 }}>
                    {new Date(n.created_at).toLocaleString("ko-KR")}
                  </div>
                </div>
                {!n.is_read && (
                  <div
                    style={{
                      width: 8, height: 8, borderRadius: "50%",
                      background: "var(--primary)", flexShrink: 0, marginTop: 4,
                    }}
                  />
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}