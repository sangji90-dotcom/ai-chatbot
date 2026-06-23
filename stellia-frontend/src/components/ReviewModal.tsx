import { useState, useEffect } from "react";
import axios from "axios";

interface ReviewModalProps {
  apiUrl: string;
  token: string;
  characterId: string;
  characterName: string;
  onClose: () => void;
}

export default function ReviewModal({ apiUrl, token, characterId, characterName, onClose }: ReviewModalProps) {
  const [reviews, setReviews] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [average, setAverage] = useState(0);
  const [distribution, setDistribution] = useState<Record<string, number>>({});
  const [myReview, setMyReview] = useState<any>(null);
  const [myRating, setMyRating] = useState(0);
  const [myContent, setMyContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {
    try {
      const res = await axios.get(`${apiUrl}/reviews/${characterId}`, { headers });
      setReviews(res.data.reviews);
      setTotal(res.data.total);
      setAverage(res.data.average);
      setDistribution(res.data.distribution);
      if (res.data.my_review) {
        setMyReview(res.data.my_review);
        setMyRating(res.data.my_review.rating);
        setMyContent(res.data.my_review.content);
      }
    } catch {
      console.error("리뷰 로드 실패");
    }
  };

  const handleSubmit = async () => {
    if (myRating === 0) return;
    setLoading(true);
    try {
      await axios.post(`${apiUrl}/reviews/${characterId}`,
        { rating: myRating, content: myContent }, { headers });
      setMsg(myReview ? "리뷰 수정 완료!" : "리뷰 작성 완료!");
      await fetchReviews();
    } catch {
      setMsg("실패했어요.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("리뷰를 삭제할까요?")) return;
    try {
      await axios.delete(`${apiUrl}/reviews/${characterId}`, { headers });
      setMyReview(null);
      setMyRating(0);
      setMyContent("");
      setMsg("리뷰 삭제 완료");
      await fetchReviews();
    } catch {
      setMsg("삭제 실패");
    }
  };

  const StarRow = ({ rating, onSelect, size = 28 }: { rating: number; onSelect?: (r: number) => void; size?: number }) => (
    <div style={{ display: "flex", gap: 4 }}>
      {[1, 2, 3, 4, 5].map(i => (
        <span key={i}
          onClick={() => onSelect?.(i)}
          style={{
            fontSize: size, cursor: onSelect ? "pointer" : "default",
            color: i <= rating ? "#ffc850" : "rgba(255,255,255,.2)",
            transition: "color .15s ease",
          }}>★</span>
      ))}
    </div>
  );

  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 60, background: "rgba(0,0,0,.7)", backdropFilter: "blur(4px)" }} />

      <div style={{
        position: "fixed", top: "50%", left: "50%",
        transform: "translate(-50%, -50%)", zIndex: 61,
        width: 500, maxWidth: "92vw", maxHeight: "85vh",
        borderRadius: 28, overflow: "hidden",
        border: "1px solid var(--border-default)",
        background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
        boxShadow: "0 0 60px rgba(0,0,0,.5)",
        display: "flex", flexDirection: "column",
      }}>

        {/* 헤더 */}
        <div style={{ padding: "24px 24px 0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontWeight: 700, fontSize: 18 }}>
            ⭐ {characterName} 리뷰
          </div>
          <button onClick={onClose} style={{
            width: 36, height: 36, borderRadius: 10,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-muted)", fontSize: 18, cursor: "pointer",
          }}>×</button>
        </div>

        <div style={{ overflowY: "auto", flex: 1, padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>

          {/* 평균 별점 + 분포 */}
          <div style={{
            borderRadius: 20, padding: 20,
            border: "1px solid var(--border-default)",
            background: "rgba(255,200,80,.05)",
            display: "flex", gap: 24, alignItems: "center",
          }}>
            <div style={{ textAlign: "center", flexShrink: 0 }}>
              <div style={{ fontSize: 48, fontWeight: 800, color: "#ffc850" }}>{average}</div>
              <StarRow rating={Math.round(average)} size={18} />
              <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 6 }}>총 {total}개 리뷰</div>
            </div>

            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
              {[5, 4, 3, 2, 1].map(star => {
                const count = distribution[String(star)] ?? 0;
                const pct = total > 0 ? (count / total) * 100 : 0;
                return (
                  <div key={star} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: "#ffc850", fontSize: 12, width: 20 }}>{star}★</span>
                    <div style={{ flex: 1, height: 6, borderRadius: 999, background: "rgba(255,255,255,.08)", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: "#ffc850", borderRadius: 999, transition: "width .4s ease" }} />
                    </div>
                    <span style={{ color: "var(--text-muted)", fontSize: 11, width: 24 }}>{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 내 리뷰 작성 */}
          {token && (
            <div style={{
              borderRadius: 20, padding: 20,
              border: "1px solid rgba(139,124,255,.3)",
              background: "rgba(139,124,255,.05)",
            }}>
              <div style={{ fontWeight: 600, marginBottom: 14 }}>
                {myReview ? "내 리뷰 수정" : "리뷰 작성"}
              </div>

              <div style={{ marginBottom: 14 }}>
                <StarRow rating={myRating} onSelect={setMyRating} size={32} />
              </div>

              <textarea
                value={myContent}
                onChange={e => setMyContent(e.target.value)}
                placeholder="리뷰를 작성해주세요 (선택)"
                style={{
                  width: "100%", padding: "12px 16px", borderRadius: 14,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-primary)", fontSize: 14,
                  outline: "none", resize: "vertical", minHeight: 80,
                  boxSizing: "border-box",
                }}
              />

              {msg && (
                <div style={{
                  color: msg.includes("실패") ? "#ff6b8a" : "#49d89a",
                  fontSize: 13, marginTop: 8,
                }}>{msg}</div>
              )}

              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button onClick={handleSubmit} disabled={loading || myRating === 0} style={{
                  flex: 1, padding: "12px", borderRadius: 12, border: "none",
                  background: myRating === 0 ? "rgba(255,255,255,.06)" : "var(--gradient-cosmic)",
                  color: myRating === 0 ? "var(--text-muted)" : "#fff",
                  fontWeight: 700, cursor: myRating === 0 ? "not-allowed" : "pointer",
                }}>
                  {loading ? "저장 중..." : myReview ? "수정하기" : "작성하기"}
                </button>
                {myReview && (
                  <button onClick={handleDelete} style={{
                    padding: "12px 16px", borderRadius: 12,
                    border: "1px solid rgba(255,107,138,.3)",
                    background: "rgba(255,107,138,.08)",
                    color: "#ff6b8a", cursor: "pointer",
                  }}>삭제</button>
                )}
              </div>
            </div>
          )}

          {/* 리뷰 목록 */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {reviews.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "30px 0" }}>
                아직 리뷰가 없어요. 첫 번째 리뷰를 작성해봐요!
              </div>
            ) : reviews.map(r => (
              <div key={r.id} style={{
                borderRadius: 16, padding: 16,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.03)",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: "50%",
                    background: r.profile_image_url ? "none" : "var(--gradient-cosmic)",
                    display: "grid", placeItems: "center",
                    fontWeight: 700, fontSize: 14, overflow: "hidden", flexShrink: 0,
                  }}>
                    {r.profile_image_url
                      ? <img src={r.profile_image_url} alt={r.username} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                      : r.username?.[0]?.toUpperCase()}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {r.equipped_prefix && <span style={{ color: "var(--primary)", marginRight: 4 }}>[{r.equipped_prefix}]</span>}
                      {r.username}
                      {r.equipped_suffix && <span style={{ color: "var(--primary)", marginLeft: 4 }}>[{r.equipped_suffix}]</span>}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                      <StarRow rating={r.rating} size={13} />
                      <span style={{ color: "var(--text-muted)", fontSize: 11 }}>
                        {new Date(r.created_at).toLocaleDateString("ko-KR")}
                      </span>
                    </div>
                  </div>
                </div>
                {r.content && (
                  <div style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.7 }}>
                    {r.content}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}