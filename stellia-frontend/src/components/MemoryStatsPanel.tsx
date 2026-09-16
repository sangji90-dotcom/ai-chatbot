import { useEffect, useState } from "react";
import axios from "axios";

/**
 * 기억 품질 지표.
 *
 * "기억을 얼마나 잘하는가" 를 감이 아니라 숫자로 본다.
 * 지표를 나열만 하면 읽는 사람이 판단을 못 하므로, 각 값 옆에
 * "이 숫자가 이러면 무슨 뜻인지" 를 함께 적는다.
 */
interface Props {
  apiUrl: string;
  token: string;
}

type Stats = {
  period_days: number;
  sessions: Record<string, number>;
  memory_book: { total: number; pairs: number };
  events: Record<string, { count: number; avg_value: number }>;
  extract_rate: number | null;
  avg_injected: number;
  forgot_reports: number;
  feedback: { likes: number; dislikes_by_reason: Record<string, number> };
};

const REASON_LABEL: Record<string, string> = {
  memory: "기억 못함",
  repetition: "반복",
  tone: "말투",
  offtopic: "엉뚱함",
  quality: "성의 없음",
  other: "기타",
  unspecified: "사유 없음",
};

export default function MemoryStatsPanel({ apiUrl, token }: Props) {
  const headers = { Authorization: `Bearer ${token}` };
  const [days, setDays] = useState(7);
  const [stats, setStats] = useState<Stats | null>(null);
  const [samples, setSamples] = useState<any[] | null>(null);
  const [openSample, setOpenSample] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    axios.get(`${apiUrl}/admin/memory-stats?days=${days}`, { headers })
      .then(r => { setStats(r.data); setError(""); })
      .catch(e => setError(e?.response?.data?.detail || "지표를 불러오지 못했어요."));
  }, [days]);

  const loadSamples = () => {
    axios.get(`${apiUrl}/admin/memory-stats/samples?limit=20`, { headers })
      .then(r => setSamples(r.data))
      .catch(() => setSamples([]));
  };

  if (error) return <div style={{ color: "#ff6b8a", padding: 20 }}>{error}</div>;
  if (!stats) return <div style={{ color: "var(--text-muted)", padding: 20 }}>불러오는 중...</div>;

  const s = stats.sessions || {};
  const totalSessions = s.sessions || 0;
  const reachedMemory = (s.turns_10_40 || 0) + (s.turns_40_100 || 0) + (s.over_100 || 0);
  const reachRate = totalSessions ? reachedMemory / totalSessions : 0;

  const card = {
    padding: 18, borderRadius: 16,
    background: "rgba(255,255,255,.04)",
    border: "1px solid var(--border-default)",
  };
  const num = (color: string) => ({
    fontSize: 26, fontWeight: 700, color, lineHeight: 1.2,
  });
  const hint = {
    fontSize: 11, color: "var(--text-muted)", marginTop: 8, lineHeight: 1.5,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>기간</span>
        {[1, 7, 30].map(d => (
          <button key={d} onClick={() => setDays(d)} style={{
            padding: "6px 14px", borderRadius: 999, fontSize: 12, cursor: "pointer",
            border: "1px solid var(--border-default)",
            background: days === d ? "linear-gradient(90deg,#ff6b8a,#ff9532)" : "transparent",
            color: days === d ? "#fff" : "var(--text-muted)",
          }}>{d}일</button>
        ))}
      </div>

      {/* 가장 중요한 지표 2개 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={card}>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>기억이 작동할 기회에 도달한 세션</div>
          <div style={num(reachRate >= 0.3 ? "#49d89a" : "#ffc850")}>
            {(reachRate * 100).toFixed(0)}%
            <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 400 }}>
              {" "}({reachedMemory}/{totalSessions} 세션)
            </span>
          </div>
          <div style={hint}>
            10턴을 못 넘기면 기억이 개입할 기회 자체가 없다.
            이 값이 낮으면 기억보다 <b>대화 재미</b>를 먼저 봐야 한다.
          </div>
        </div>

        <div style={card}>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>"기억 못함" 신고</div>
          <div style={num(stats.forgot_reports === 0 ? "#49d89a" : "#ff6b8a")}>
            {stats.forgot_reports}건
          </div>
          <div style={hint}>
            유저가 직접 누른 신고. <b>가장 직접적인 신호</b>다.
            개선이 먹히면 이 수치가 떨어진다.
          </div>
        </div>
      </div>

      {/* 세션 길이 분포 */}
      <div style={card}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
          세션 길이 분포 (평균 {s.avg_turns ?? 0}턴)
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {[
            { k: "under_10", label: "~9턴", color: "#6b7280" },
            { k: "turns_10_40", label: "10~39턴", color: "#8b7cff" },
            { k: "turns_40_100", label: "40~99턴", color: "#5fd6ff" },
            { k: "over_100", label: "100턴+", color: "#49d89a" },
          ].map(b => {
            const v = s[b.k] || 0;
            const pct = totalSessions ? (v / totalSessions) * 100 : 0;
            return (
              <div key={b.k} style={{ flex: 1 }}>
                <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,.08)" }}>
                  <div style={{ width: `${pct}%`, height: "100%", borderRadius: 3, background: b.color }} />
                </div>
                <div style={{ fontSize: 11, marginTop: 6, color: "var(--text-muted)" }}>
                  {b.label} · <b style={{ color: b.color }}>{v}</b>
                </div>
              </div>
            );
          })}
        </div>
        <div style={hint}>100턴을 넘으면 자동 요약이 발동해 이전 대화가 압축된다.</div>
      </div>

      {/* 추출 / 주입 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={card}>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>기억 추출 성공률</div>
          <div style={num("#8b7cff")}>
            {stats.extract_rate == null ? "—" : `${(stats.extract_rate * 100).toFixed(0)}%`}
          </div>
          <div style={hint}>
            추출을 시도한 구간 중 실제로 기억이 남은 비율.<br />
            <b>0.2 미만</b> = 프롬프트가 너무 보수적 · <b>0.9 이상</b> = 쓸데없는 것까지 줍는 중
          </div>
        </div>
        <div style={card}>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>요청당 주입 기억 수</div>
          <div style={num("#5fd6ff")}>{stats.avg_injected}</div>
          <div style={hint}>
            상한(무료 20개)에 계속 붙어 있으면 상한이 병목이다.
            올리거나 중요도 선별이 필요하다.
          </div>
        </div>
      </div>

      {/* 이벤트 원본 */}
      <div style={card}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10 }}>이벤트</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {Object.entries(stats.events).map(([k, v]) => (
            <span key={k} style={{
              fontSize: 11, padding: "5px 10px", borderRadius: 999,
              background: k.includes("fail") ? "rgba(255,107,138,.15)" : "rgba(139,124,255,.12)",
              border: `1px solid ${k.includes("fail") ? "rgba(255,107,138,.4)" : "rgba(139,124,255,.3)"}`,
            }}>
              {k} · <b>{v.count}</b>
            </span>
          ))}
          {Object.keys(stats.events).length === 0 && (
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              아직 기록된 이벤트가 없어요. 10턴 이상 대화하면 쌓이기 시작합니다.
            </span>
          )}
        </div>
        <div style={hint}>
          <code>summarize</code> 가 발동한 뒤 "기억 못함" 신고가 늘면 요약이 범인이다.
          <code>AUTO_SUMMARY_THRESHOLD</code> 를 조정할 것.
        </div>
      </div>

      {/* 피드백 사유 */}
      <div style={card}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10 }}>
          피드백 (👍 {stats.feedback.likes})
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {Object.entries(stats.feedback.dislikes_by_reason).map(([k, v]) => (
            <span key={k} style={{
              fontSize: 12, padding: "6px 12px", borderRadius: 999,
              background: k === "memory" ? "rgba(255,107,138,.18)" : "rgba(255,255,255,.06)",
              border: "1px solid var(--border-default)",
            }}>
              {REASON_LABEL[k] || k} · <b>{v}</b>
            </span>
          ))}
          {Object.keys(stats.feedback.dislikes_by_reason).length === 0 && (
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>아직 없음</span>
          )}
        </div>
      </div>

      {/* 신고 샘플 — 원인 분석 */}
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>"기억 못함" 신고 샘플</span>
          <button onClick={loadSamples} style={{
            fontSize: 11, padding: "6px 12px", borderRadius: 999, cursor: "pointer",
            border: "1px solid var(--border-default)", background: "transparent",
            color: "var(--text-primary)",
          }}>불러오기</button>
        </div>
        <div style={hint}>
          신고된 메시지의 직전 대화와 <b>그 시점에 실제로 주입돼 있던 기억</b>을 나란히 본다.
          추출이 안 된 건지 / 됐는데 AI가 안 쓴 건지 / 상한에 밀린 건지가 여기서 갈린다.
        </div>

        {samples && samples.length === 0 && (
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 12 }}>신고 샘플이 없어요.</div>
        )}

        {samples?.map(sm => (
          <div key={sm.message_id} style={{
            marginTop: 12, padding: 14, borderRadius: 12,
            background: "rgba(0,0,0,.25)", border: "1px solid var(--border-subtle)",
          }}>
            <div
              onClick={() => setOpenSample(openSample === sm.message_id ? null : sm.message_id)}
              style={{ cursor: "pointer", fontSize: 13 }}
            >
              <span style={{ color: "#ff6b8a" }}>▸</span>{" "}
              {String(sm.reported_message).slice(0, 70)}...
              <span style={{ float: "right", fontSize: 11, color: "var(--text-muted)" }}>
                {String(sm.created_at).slice(0, 16)}
              </span>
            </div>

            {openSample === sm.message_id && (
              <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6 }}>직전 대화</div>
                  {sm.context_before?.map((m: any, i: number) => (
                    <div key={i} style={{ fontSize: 12, marginBottom: 4 }}>
                      <b style={{ color: m.role === "user" ? "#5fd6ff" : "#49d89a" }}>
                        {m.role === "user" ? "유저" : "캐릭터"}
                      </b>{" "}
                      <span style={{ color: "var(--text-primary)" }}>
                        {String(m.content).slice(0, 120)}
                      </span>
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6 }}>
                    그 시점 보유 기억 ({sm.memories_at_the_time?.length || 0}개)
                  </div>
                  {sm.memories_at_the_time?.length
                    ? sm.memories_at_the_time.map((m: string, i: number) => (
                        <div key={i} style={{ fontSize: 12, color: "var(--text-primary)" }}>· {m}</div>
                      ))
                    : <div style={{ fontSize: 12, color: "#ff6b8a" }}>
                        기억이 하나도 없음 — 추출 단계에서 실패한 케이스
                      </div>}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
