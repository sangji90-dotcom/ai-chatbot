import { useState, useEffect } from "react";
import axios from "axios";

interface CoinModalProps {
  apiUrl: string;
  token: string;
  onClose: () => void;
  onCoinsUpdated: (balance: number) => void;
}

const TOKEN_PACKAGES = [
  { id: 1, price: 1900, token_amount: 2000, label: "2,000 금화", bonus: "" },
  { id: 2, price: 3800, token_amount: 4200, label: "4,200 금화", bonus: "+200 보너스" },
  { id: 3, price: 9500, token_amount: 11000, label: "11,000 금화", bonus: "+1,000 보너스" },
  { id: 4, price: 19000, token_amount: 23000, label: "23,000 금화", bonus: "+3,000 보너스" },
];

export default function CoinModal({ apiUrl, token, onClose, onCoinsUpdated }: CoinModalProps) {
  const [coinData, setCoinData] = useState<any>(null);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [memoryPass, setMemoryPass] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [attended, setAttended] = useState(false);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState<"coins" | "shop" | "memory">("coins");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/tokens/me`, { headers })
      .then(res => setCoinData(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/users/me`, { headers })
      .then(res => {
        setUserInfo(res.data);
        const today = new Date().toISOString().slice(0, 10);
        setAttended(res.data.last_attendance_date === today);
      })
      .catch(console.error);

    axios.get(`${apiUrl}/tokens/memory-pass/status`, { headers })
      .then(res => setMemoryPass(res.data))
      .catch(console.error);
  }, []);

  const refreshCoins = async () => {
    const coinRes = await axios.get(`${apiUrl}/tokens/me`, { headers });
    setCoinData(coinRes.data);
    onCoinsUpdated(coinRes.data.token_balance);
  };

  const handleAttendance = async () => {
    setLoading(true);
    setMessage("");
    try {
      const res = await axios.post(`${apiUrl}/tokens/attendance`, {}, { headers });
      setMessage(res.data.message);
      setAttended(true);
      await refreshCoins();
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

  const handlePurchase = async (packageId: number) => {
    setLoading(true);
    setMessage("");
    try {
      const res = await axios.post(`${apiUrl}/tokens/purchase/${packageId}`, {}, { headers });
      setMessage(res.data.message);
      await refreshCoins();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setMessage(err.response?.data?.detail || "구매에 실패했어요.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMemoryPassCash = async () => {
    if (!confirm("메모리 패스 30일권을 9,900원에 구매할까요?\n(테스트 모드 — 실제 결제 없이 지급)")) return;
    setLoading(true);
    setMessage("");
    try {
      const res = await axios.post(`${apiUrl}/tokens/memory-pass/purchase-cash`, {}, { headers });
      setMessage(res.data.message);
      const passRes = await axios.get(`${apiUrl}/tokens/memory-pass/status`, { headers });
      setMemoryPass(passRes.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setMessage(err.response?.data?.detail || "구매에 실패했어요.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMemoryPassCoin = async () => {
    if (!confirm("메모리 패스 30일권을 금화 24,900개로 구매할까요?\n메모리 청크 5개가 추가로 지급돼요!")) return;
    setLoading(true);
    setMessage("");
    try {
      const res = await axios.post(`${apiUrl}/tokens/memory-pass/purchase`, {}, { headers });
      setMessage(res.data.message);
      await refreshCoins();
      const passRes = await axios.get(`${apiUrl}/tokens/memory-pass/status`, { headers });
      setMemoryPass(passRes.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setMessage(err.response?.data?.detail || "구매에 실패했어요.");
      }
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: "coins", label: "💰 내 코인" },
    { id: "shop", label: "🛒 충전소" },
    { id: "memory", label: "🧠 메모리 패스" },
  ] as const;

  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,.6)", backdropFilter: "blur(4px)" }} />

      <div style={{
        position: "fixed", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)", zIndex: 51,
        width: 460, maxWidth: "90vw", maxHeight: "85vh",
        borderRadius: 28,
        border: "1px solid rgba(246,198,91,.3)",
        background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
        boxShadow: "0 0 60px rgba(246,198,91,.15), 0 0 30px rgba(0,0,0,.5)",
        overflow: "hidden", display: "flex", flexDirection: "column",
      }}>
        {/* 헤더 */}
        <div style={{ padding: "24px 24px 0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: "var(--gold)", textShadow: "0 0 20px rgba(246,198,91,.4)" }}>
            ✦ 럭키 코인
          </div>
          <button onClick={onClose} style={{
            width: 36, height: 36, borderRadius: 10,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-muted)", fontSize: 18, cursor: "pointer",
          }}>×</button>
        </div>

        {/* 탭 */}
        <div style={{ display: "flex", margin: "16px 24px 0", borderRadius: 14, background: "rgba(255,255,255,.04)", border: "1px solid var(--border-default)", overflow: "hidden" }}>
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              flex: 1, padding: "10px", border: "none",
              background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 12, cursor: "pointer",
            }}>{tab.label}</button>
          ))}
        </div>

        <div style={{ padding: 24, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>

          {/* 메시지 */}
          {message && (
            <div style={{
              padding: "12px 16px", borderRadius: 12,
              background: message.includes("실패") || message.includes("부족") ? "rgba(255,107,138,.1)" : "rgba(73,216,154,.1)",
              border: `1px solid ${message.includes("실패") || message.includes("부족") ? "rgba(255,107,138,.3)" : "rgba(73,216,154,.3)"}`,
              color: message.includes("실패") || message.includes("부족") ? "#ff6b8a" : "#49d89a",
              fontSize: 13, textAlign: "center",
            }}>{message}</div>
          )}

          {/* 내 코인 탭 */}
          {activeTab === "coins" && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div style={{
                  borderRadius: 18, padding: 18,
                  background: "linear-gradient(135deg, rgba(246,198,91,.18), rgba(246,198,91,.05))",
                  border: "1px solid rgba(246,198,91,.3)",
                }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>🥇</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>금화 (구매)</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "var(--gold)" }}>
                    {coinData?.token_purchased?.toLocaleString() ?? 0}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 4 }}>만료 없음</div>
                </div>
                <div style={{
                  borderRadius: 18, padding: 18,
                  background: "linear-gradient(135deg, rgba(200,200,220,.12), rgba(200,200,220,.04))",
                  border: "1px solid rgba(200,200,220,.2)",
                }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>🥈</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>은화 (보너스)</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "#c8c8dc" }}>
                    {coinData?.token_event?.toLocaleString() ?? 0}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 4 }}>21일 만료</div>
                </div>
              </div>

              <div style={{
                borderRadius: 18, padding: 16,
                background: "rgba(255,255,255,.03)",
                border: "1px solid var(--border-default)",
                display: "flex", alignItems: "center", justifyContent: "space-between",
              }}>
                <div style={{ color: "var(--text-muted)", fontSize: 14 }}>총 잔액</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: "var(--gold)" }}>
                  ✦ {coinData?.token_balance?.toLocaleString() ?? 0}
                </div>
              </div>

              {/* 출석 체크 */}
              <div style={{ borderRadius: 18, padding: 20, background: "rgba(255,255,255,.02)", border: "1px solid var(--border-default)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 15 }}>출석 체크</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>매일 출석하면 은화 1,000개를 드려요</div>
                  </div>
                  {userInfo?.attendance_streak > 0 && (
                    <div style={{
                      padding: "6px 12px", borderRadius: 999,
                      background: "rgba(139,124,255,.12)",
                      border: "1px solid rgba(139,124,255,.2)",
                      color: "var(--primary)", fontSize: 13, fontWeight: 600,
                    }}>🔥 {userInfo.attendance_streak}일 연속</div>
                  )}
                </div>
                <button onClick={handleAttendance} disabled={attended || loading} style={{
                  width: "100%", padding: "14px", borderRadius: 14,
                  border: attended ? "1px solid var(--border-default)" : "1px solid rgba(246,198,91,.4)",
                  background: attended ? "rgba(255,255,255,.06)" : "linear-gradient(135deg, rgba(246,198,91,.3), rgba(246,198,91,.15))",
                  color: attended ? "var(--text-muted)" : "var(--gold)",
                  fontWeight: 700, fontSize: 15,
                  cursor: attended ? "not-allowed" : "pointer",
                }}>
                  {loading ? "처리 중..." : attended ? "오늘 출석 완료 ✓" : "출석 체크 +1,000 🥈"}
                </button>
              </div>

              <div style={{ color: "var(--text-muted)", fontSize: 12, textAlign: "center", lineHeight: 1.6 }}>
                은화는 구매한 금화보다 먼저 사용돼요.<br />
                은화는 지급일로부터 21일 후 만료돼요.
              </div>
            </>
          )}

          {/* 충전소 탭 */}
          {activeTab === "shop" && (
            <>
              <div style={{ color: "var(--text-muted)", fontSize: 13, textAlign: "center" }}>
                금화를 충전해서 캐릭터와 더 많이 대화해요!<br />
                <span style={{ color: "#ff6b8a", fontSize: 12 }}>※ 현재 테스트 모드 — 실제 결제 없이 지급됩니다</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {TOKEN_PACKAGES.map(pkg => (
                  <button key={pkg.id} onClick={() => handlePurchase(pkg.id)} disabled={loading} style={{
                    padding: "16px 20px", borderRadius: 16,
                    border: "1px solid rgba(246,198,91,.3)",
                    background: "linear-gradient(135deg, rgba(246,198,91,.08), rgba(246,198,91,.03))",
                    cursor: loading ? "not-allowed" : "pointer",
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                  }}>
                    <div style={{ textAlign: "left" }}>
                      <div style={{ fontWeight: 700, color: "var(--gold)", fontSize: 15 }}>🥇 {pkg.label}</div>
                      {pkg.bonus && <div style={{ color: "#49d89a", fontSize: 12, marginTop: 3 }}>{pkg.bonus}</div>}
                    </div>
                    <div style={{
                      padding: "8px 16px", borderRadius: 10,
                      background: "rgba(246,198,91,.2)",
                      color: "var(--gold)", fontWeight: 700, fontSize: 14,
                    }}>{pkg.price.toLocaleString()}원</div>
                  </button>
                ))}
              </div>
            </>
          )}

          {/* 메모리 패스 탭 */}
          {activeTab === "memory" && (
            <>
              {/* 현재 상태 */}
              <div style={{
                borderRadius: 20, padding: 20,
                background: memoryPass?.active
                  ? "linear-gradient(135deg, rgba(139,124,255,.2), rgba(95,214,255,.1))"
                  : "rgba(255,255,255,.03)",
                border: `1px solid ${memoryPass?.active ? "rgba(139,124,255,.4)" : "var(--border-default)"}`,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                  <div style={{ fontSize: 32 }}>🧠</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>메모리 패스</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2 }}>
                      {memoryPass?.active ? `활성화 중 · ${memoryPass.expires_at}까지` : "비활성화"}
                    </div>
                  </div>
                  {memoryPass?.active && (
                    <div style={{
                      marginLeft: "auto", padding: "4px 10px", borderRadius: 999,
                      background: "rgba(73,216,154,.15)", border: "1px solid rgba(73,216,154,.3)",
                      color: "#49d89a", fontSize: 12, fontWeight: 600,
                    }}>활성</div>
                  )}
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.7 }}>
                  • AI가 중요한 대화 내용을 자동으로 기억해요<br />
                  • 메모리 청크 최대 {memoryPass?.chunk_limit ?? 20}개 저장<br />
                  • 장기 대화에서도 맥락을 유지해요
                </div>
              </div>

              {/* 구매 옵션 비교 */}
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>

                {/* 현금 구매 */}
                <div style={{
                  borderRadius: 16, padding: 18,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.03)",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>💳 현금 구매</div>
                      <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                        30일권
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontWeight: 700, fontSize: 18, color: "var(--text-primary)" }}>9,900원</div>
                    </div>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 12 }}>
                    • 메모리 청크 20개
                  </div>
                  <button onClick={handleMemoryPassCash} disabled={loading} style={{
                    width: "100%", padding: "12px", borderRadius: 12, border: "none",
                    background: "rgba(255,255,255,.08)",
                    color: "var(--text-primary)", fontWeight: 600, fontSize: 14,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}>
                    {memoryPass?.active ? "30일 연장" : "구매하기"}
                  </button>
                </div>

                {/* 금화 구매 — 추천 */}
                <div style={{
                  borderRadius: 16, padding: 18,
                  border: "1px solid rgba(246,198,91,.4)",
                  background: "linear-gradient(135deg, rgba(246,198,91,.1), rgba(246,198,91,.04))",
                  position: "relative", overflow: "hidden",
                }}>
                  {/* 추천 뱃지 */}
                  <div style={{
                    position: "absolute", top: 12, right: 12,
                    padding: "3px 10px", borderRadius: 999, fontSize: 11,
                    background: "rgba(246,198,91,.3)", color: "var(--gold)", fontWeight: 700,
                    zIndex: 1,
                }}>🔥 추천</div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15, color: "var(--gold)" }}>🥇 금화 구매</div>
                      <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                        30일권 + 보너스
                      </div>
                    </div>
                    <div style={{ textAlign: "right", paddingRight: 56 }}>
                      <div style={{ fontWeight: 700, fontSize: 18, color: "var(--gold)" }}>24,900 금화</div>
                      <div style={{ color: "#49d89a", fontSize: 11, marginTop: 2 }}>≈ 약 8,200원 상당</div>
                    </div>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 12 }}>
                    • 메모리 청크 20개 기본<br />
                    • <span style={{ color: "#49d89a", fontWeight: 600 }}>보너스 청크 5개 추가 지급</span><br />
                    • 현금보다 약 17% 저렴
                  </div>
                  <button onClick={handleMemoryPassCoin} disabled={loading} style={{
                    width: "100%", padding: "12px", borderRadius: 12, border: "none",
                    background: "linear-gradient(135deg, rgba(246,198,91,.4), rgba(246,198,91,.2))",
                    color: "var(--gold)", fontWeight: 700, fontSize: 14,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}>
                    {memoryPass?.active ? "30일 연장 + 청크 5개" : "구매하기 + 청크 5개"}
                  </button>
                </div>
              </div>

              {/* 청크 추가 */}
              {memoryPass?.active && (
                <div style={{
                  borderRadius: 16, padding: 16,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.03)",
                }}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>메모리 청크 추가</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12 }}>
                    현재 {memoryPass.chunk_limit}개 / 최대 100개 · 금화 1개 = 청크 1개
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {[5, 10, 20].map(n => (
                      <button key={n} onClick={async () => {
                        setLoading(true);
                        try {
                          await axios.post(`${apiUrl}/tokens/memory-pass/add-chunk?amount=${n}`, {}, { headers });
                          setMessage(`메모리 청크 ${n}개 추가 완료`);
                          await refreshCoins();
                          const passRes = await axios.get(`${apiUrl}/tokens/memory-pass/status`, { headers });
                          setMemoryPass(passRes.data);
                        } catch (err) {
                          if (axios.isAxiosError(err)) setMessage(err.response?.data?.detail || "실패");
                        } finally {
                          setLoading(false);
                        }
                      }} disabled={loading} style={{
                        flex: 1, padding: "10px", borderRadius: 12,
                        border: "1px solid rgba(139,124,255,.3)",
                        background: "rgba(139,124,255,.08)",
                        color: "var(--primary)", fontWeight: 600, fontSize: 13,
                        cursor: "pointer",
                      }}>+{n}개 ({n}금화)</button>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ color: "var(--text-muted)", fontSize: 12, textAlign: "center", lineHeight: 1.6 }}>
                만료 전 구매 시 남은 기간에 30일이 추가돼요.<br />
                금화 구매 시 보너스 청크는 즉시 지급돼요.
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}