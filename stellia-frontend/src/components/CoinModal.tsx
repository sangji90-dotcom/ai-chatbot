import { useState, useEffect } from "react";
import axios from "axios";

interface CoinModalProps {
  apiUrl: string;
  token: string;
  onClose: () => void;
  onCoinsUpdated: (balance: number) => void;
}

export default function CoinModal({ apiUrl, token, onClose, onCoinsUpdated }: CoinModalProps) {
  const [coinData, setCoinData] = useState<any>(null);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [attended, setAttended] = useState(false);
  const [message, setMessage] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    // 코인 정보
    axios.get(`${apiUrl}/tokens/me`, { headers })
      .then(res => setCoinData(res.data))
      .catch(console.error);

    // 유저 정보 (출석 여부)
    axios.get(`${apiUrl}/users/me`, { headers })
      .then(res => {
        setUserInfo(res.data);
        const today = new Date().toISOString().slice(0, 10);
        setAttended(res.data.last_attendance_date === today);
      })
      .catch(console.error);
  }, []);

  const handleAttendance = async () => {
    setLoading(true);
    setMessage("");
    try {
      const res = await axios.post(`${apiUrl}/tokens/attendance`, {}, { headers });
      setMessage(res.data.message);
      setAttended(true);

      // 코인 잔액 갱신
      const coinRes = await axios.get(`${apiUrl}/tokens/me`, { headers });
      setCoinData(coinRes.data);
      onCoinsUpdated(coinRes.data.token_balance);

      // 유저 정보 갱신
      const userRes = await axios.get(`${apiUrl}/users/me`, { headers });
      setUserInfo(userRes.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setMessage(err.response?.data?.detail || "오류가 발생했어요.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* 오버레이 */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.6)",
          backdropFilter: "blur(4px)",
        }}
      />

      {/* 모달 */}
      <div
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 420,
          maxWidth: "90vw",
          borderRadius: 28,
          border: "1px solid rgba(246,198,91,.3)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(246,198,91,.15), 0 0 30px rgba(0,0,0,.5)",
          overflow: "hidden",
        }}
      >
        {/* 헤더 */}
        <div
          style={{
            padding: "24px 24px 0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{
              fontSize: 20, fontWeight: 700,
              color: "var(--gold)",
              textShadow: "0 0 20px rgba(246,198,91,.4)",
            }}
          >
            ✦ 럭키 코인
          </div>
          <button
            onClick={onClose}
            style={{
              width: 36, height: 36, borderRadius: 10,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)",
              fontSize: 18, cursor: "pointer",
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
          {/* 금화 / 은화 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {/* 금화 */}
            <div
              style={{
                borderRadius: 18, padding: 18,
                background: "linear-gradient(135deg, rgba(246,198,91,.18), rgba(246,198,91,.05))",
                border: "1px solid rgba(246,198,91,.3)",
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 8 }}>🥇</div>
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>금화 (구매)</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "var(--gold)" }}>
                {coinData?.token_purchased?.toLocaleString() ?? 0}
              </div>
            </div>

            {/* 은화 */}
            <div
              style={{
                borderRadius: 18, padding: 18,
                background: "linear-gradient(135deg, rgba(200,200,220,.12), rgba(200,200,220,.04))",
                border: "1px solid rgba(200,200,220,.2)",
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 8 }}>🥈</div>
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>은화 (보너스)</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#c8c8dc" }}>
                {coinData?.token_event?.toLocaleString() ?? 0}
              </div>
            </div>
          </div>

          {/* 총 잔액 */}
          <div
            style={{
              borderRadius: 18, padding: 16,
              background: "rgba(255,255,255,.03)",
              border: "1px solid var(--border-default)",
              display: "flex", alignItems: "center", justifyContent: "space-between",
            }}
          >
            <div style={{ color: "var(--text-muted)", fontSize: 14 }}>총 잔액</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--gold)" }}>
              ✦ {coinData?.token_balance?.toLocaleString() ?? 0}
            </div>
          </div>

          {/* 출석 체크 */}
          <div
            style={{
              borderRadius: 18, padding: 20,
              background: "rgba(255,255,255,.02)",
              border: "1px solid var(--border-default)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 15 }}>출석 체크</div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
                  매일 출석하면 은화 1,000개를 드려요
                </div>
              </div>
              {userInfo?.attendance_streak > 0 && (
                <div
                  style={{
                    padding: "6px 12px", borderRadius: 999,
                    background: "rgba(139,124,255,.12)",
                    border: "1px solid rgba(139,124,255,.2)",
                    color: "var(--primary)", fontSize: 13, fontWeight: 600,
                  }}
                >
                  🔥 {userInfo.attendance_streak}일 연속
                </div>
              )}
            </div>

            {message && (
              <div style={{ color: message.includes("완료") ? "var(--gold)" : "#ff6b8a", fontSize: 13, marginBottom: 12 }}>
                {message}
              </div>
            )}

        <button
          onClick={handleAttendance}
          disabled={attended || loading}
          style={{
                width: "100%", padding: "14px",
                borderRadius: 14,
                border: attended ? "1px solid var(--border-default)" : "1px solid rgba(246,198,91,.4)",
                background: attended
                  ? "rgba(255,255,255,.06)"
                  : "linear-gradient(135deg, rgba(246,198,91,.3), rgba(246,198,91,.15))",
                color: attended ? "var(--text-muted)" : "var(--gold)",
                fontWeight: 700, fontSize: 15,
                cursor: attended ? "not-allowed" : "pointer",
                transition: "all .2s ease",
              }}
            >
              {loading ? "처리 중..." : attended ? "오늘 출석 완료 ✓" : "출석 체크 +1,000 🥈"}
            </button>
          </div>

          {/* 안내 */}
          <div style={{ color: "var(--text-muted)", fontSize: 12, textAlign: "center", lineHeight: 1.6 }}>
            은화는 구매한 금화보다 먼저 사용돼요.<br />
            은화는 지급일로부터 21일 후 만료돼요.
          </div>
        </div>
      </div>
    </>
  );
}