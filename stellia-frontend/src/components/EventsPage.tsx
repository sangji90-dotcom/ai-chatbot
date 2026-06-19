import { useState, useEffect } from "react";
import axios from "axios";

interface EventsPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
}

export default function EventsPage({ apiUrl, token, onBack }: EventsPageProps) {
  const headers = { Authorization: `Bearer ${token}` };
  
  const [referralCode, setReferralCode] = useState("");
  const [inputCode, setInputCode] = useState("");
  const [attendanceStreak, setAttendanceStreak] = useState(0);
  const [purchaseStreak, setPurchaseStreak] = useState(0);
  const [streakRewardClaimed, setStreakRewardClaimed] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [silverExpiring, setSilverExpiring] = useState<{amount: number, days_left: number | null} | null>(null);
  

  useEffect(() => {
  // 초대 코드 조회
  axios.get(`${apiUrl}/events/referral-code`, { headers })
    .then(res => setReferralCode(res.data.code))
    .catch(console.error);

    // 유저 정보 (streak + 은화 만료)
  axios.get(`${apiUrl}/users/me`, { headers })
    .then(res => {
      setAttendanceStreak(res.data.attendance_streak ?? 0);
      setPurchaseStreak(res.data.consecutive_purchase_days ?? 0);
      if (res.data.silver_expiring?.amount > 0) {
        setSilverExpiring(res.data.silver_expiring);
      }
      if (res.data.streak_reward_claimed_at) {
        const claimedDate = new Date(res.data.streak_reward_claimed_at).toDateString();
        const today = new Date().toDateString();
        setStreakRewardClaimed(claimedDate === today);
      }
    })
    .catch(console.error);
}, []);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(referralCode);
    setMsg("초대 코드가 복사됐어요!");
    setTimeout(() => setMsg(""), 2000);
  };

  const handleUseCode = async () => {
    if (!inputCode.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${apiUrl}/events/referral/use`,
        { code: inputCode.trim().toUpperCase() }, { headers });
      setMsg(res.data.message);
    } catch (e: any) {
      setMsg(e.response?.data?.detail ?? "오류가 발생했어요.");
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(""), 3000);
    }
  };

  const handleClaimStreakReward = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${apiUrl}/events/attendance-streak-reward`, {}, { headers });
      setMsg(res.data.message);
      setStreakRewardClaimed(true);
    } catch (e: any) {
      setMsg(e.response?.data?.detail ?? "오류가 발생했어요.");
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(""), 3000);
    }
  };

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
        }}>이벤트</span>
      </nav>

      <div style={{ maxWidth: 720, margin: "40px auto", padding: "0 24px", display: "flex", flexDirection: "column", gap: 24 }}>

        {/* 메시지 토스트 */}
        {msg && (
          <div style={{
            padding: "12px 20px", borderRadius: 12,
            background: "rgba(139,124,255,.2)",
            border: "1px solid rgba(139,124,255,.4)",
            color: "var(--text-primary)", fontSize: 14, textAlign: "center",
          }}>{msg}</div>
        )}

        {/* 7일 연속 출석 */}
        <EventCard title="🗓 7일 연속 출석" badge="은화 5,000">
        {silverExpiring && silverExpiring.amount > 0 && (
    <div style={{
                padding: "10px 16px", borderRadius: 10, marginBottom: 16,
                background: "rgba(255,150,50,.12)",
                border: "1px solid rgba(255,150,50,.3)",
                color: "#ff9532", fontSize: 13,
            }}>
              ⚠ 은화 {silverExpiring.amount.toLocaleString()}개가 {silverExpiring.days_left}일 후 만료돼요!
    </div>
            )}
  <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}></p>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}>
            7일 연속 출석체크 시 은화 5,000개를 드려요. (21일 내 사용)
          </p>
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} style={{
                flex: 1, height: 8, borderRadius: 999,
                background: i < attendanceStreak
                  ? "var(--gradient-cosmic)"
                  : "rgba(255,255,255,.08)",
                transition: "background .3s",
              }} />
            ))}
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>
            {attendanceStreak}/7일 달성
          </div>
          <button
            onClick={handleClaimStreakReward}
            disabled={attendanceStreak < 7 || streakRewardClaimed || loading}
            style={{
              width: "100%", padding: "12px", borderRadius: 12,
              border: "none", fontWeight: 700, fontSize: 14, cursor: "pointer",
              background: attendanceStreak >= 7 && !streakRewardClaimed
                ? "var(--gradient-cosmic)" : "rgba(255,255,255,.06)",
              color: attendanceStreak >= 7 && !streakRewardClaimed
                ? "#fff" : "var(--text-muted)",
            }}
          >
            {streakRewardClaimed ? "오늘 수령 완료" : attendanceStreak >= 7 ? "보상 수령" : `${7 - attendanceStreak}일 남음`}
          </button>
        </EventCard>

        {/* 5일 연속 결제 */}
        <EventCard title="💳 5일 연속 결제" badge="평균 구매량 50% 금화">
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 16 }}>
            5일 연속 결제 시 5일간 평균 구매 토큰의 50%를 금화로 추가 지급해요.
          </p>
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} style={{
                flex: 1, height: 8, borderRadius: 999,
                background: i < purchaseStreak
                  ? "linear-gradient(90deg, #ffc850, #ff9500)"
                  : "rgba(255,255,255,.08)",
                transition: "background .3s",
              }} />
            ))}
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
            {purchaseStreak}/5일 달성 · 결제 시 자동 지급
          </div>
        </EventCard>

        {/* 친구 초대 */}
        <EventCard title="👥 친구 초대" badge="금화 500">
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 20 }}>
            친구가 내 코드로 가입하면 나는 금화 500개, 친구는 금화 300개를 받아요.
          </p>

          {/* 내 코드 */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>내 초대 코드</div>
            <div style={{ display: "flex", gap: 10 }}>
              <div style={{
                flex: 1, padding: "12px 16px", borderRadius: 12,
                background: "rgba(255,255,255,.04)",
                border: "1px solid var(--border-default)",
                color: "var(--text-primary)", fontSize: 18,
                fontWeight: 700, letterSpacing: "0.1em",
              }}>
                {referralCode || "로딩 중..."}
              </div>
              <button onClick={handleCopyCode} style={{
                padding: "12px 20px", borderRadius: 12,
                border: "1px solid rgba(139,124,255,.4)",
                background: "rgba(139,124,255,.12)",
                color: "var(--primary)", fontSize: 13,
                fontWeight: 600, cursor: "pointer",
              }}>복사</button>
            </div>
          </div>

          {/* 코드 입력 */}
          <div>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>초대 코드 입력</div>
            <div style={{ display: "flex", gap: 10 }}>
              <input
                value={inputCode}
                onChange={e => setInputCode(e.target.value.toUpperCase())}
                placeholder="XXXXXXXX"
                maxLength={8}
                style={{
                  flex: 1, padding: "12px 16px", borderRadius: 12,
                  background: "rgba(255,255,255,.04)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)", fontSize: 15,
                  fontWeight: 600, letterSpacing: "0.1em",
                  outline: "none",
                }}
              />
              <button
                onClick={handleUseCode}
                disabled={loading || inputCode.length < 8}
                style={{
                  padding: "12px 20px", borderRadius: 12,
                  border: "none",
                  background: inputCode.length === 8 ? "var(--gradient-cosmic)" : "rgba(255,255,255,.06)",
                  color: inputCode.length === 8 ? "#fff" : "var(--text-muted)",
                  fontSize: 13, fontWeight: 600, cursor: "pointer",
                }}
              >적용</button>
            </div>
          </div>
        </EventCard>

      </div>
    </div>
  );
}

function EventCard({ title, badge, children }: {
  title: string;
  badge: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{
      borderRadius: 20,
      border: "1px solid var(--border-default)",
      background: "rgba(17,21,40,.7)",
      backdropFilter: "blur(16px)",
      padding: "24px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>{title}</span>
        <span style={{
          padding: "4px 12px", borderRadius: 999,
          background: "rgba(255,200,80,.12)",
          border: "1px solid rgba(255,200,80,.3)",
          color: "#ffc850", fontSize: 12, fontWeight: 600,
        }}>{badge}</span>
      </div>
      {children}
    </div>
  );
}