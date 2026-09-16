import { useState } from "react";
import axios from "axios";

/**
 * AI 메시지에 대한 좋아요/싫어요 + 사유 태그.
 *
 * 사유가 없으면 dislike 가 "기억을 못한다" 인지 "말투가 이상하다" 인지 구분할 수 없어
 * 기억 품질을 측정할 수 없다. CBT 의 핵심 계측 경로라 사유를 반드시 받는다.
 */
const REASONS = [
  { code: "memory", label: "앞서 한 얘기를 기억 못해요" },
  { code: "repetition", label: "같은 말을 반복해요" },
  { code: "tone", label: "말투가 캐릭터랑 안 맞아요" },
  { code: "offtopic", label: "엉뚱한 소리를 해요" },
  { code: "quality", label: "너무 짧거나 성의 없어요" },
  { code: "other", label: "기타" },
];

interface Props {
  apiUrl: string;
  token: string;
  sessionId: string;
  messageId: number;
}

export default function MessageFeedback({ apiUrl, token, sessionId, messageId }: Props) {
  const [sent, setSent] = useState<"like" | "dislike" | null>(null);
  const [picking, setPicking] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const send = async (rating: "like" | "dislike", reason = "") => {
    setSent(rating);
    setPicking(false);
    try {
      await axios.post(
        `${apiUrl}/chat/rating`,
        { session_id: sessionId, message_id: messageId, rating, reason },
        { headers }
      );
    } catch {
      // 피드백 실패가 대화를 방해하면 안 된다 — 조용히 넘긴다
    }
  };

  const btn = (active: boolean): React.CSSProperties => ({
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "2px 5px",
    fontSize: 13,
    lineHeight: 1,
    opacity: active ? 1 : 0.35,
    transition: "opacity .15s",
  });

  if (sent === "like") {
    return <span style={{ fontSize: 11, color: "var(--text-muted)", paddingLeft: 4 }}>피드백 고마워요</span>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, paddingLeft: 4 }}>
      {sent !== "dislike" && (
        <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
          <button style={btn(false)} onClick={() => send("like")} aria-label="좋아요" title="좋아요">👍</button>
          <button style={btn(picking)} onClick={() => setPicking(v => !v)} aria-label="싫어요" title="아쉬운 점 알려주기">👎</button>
        </div>
      )}

      {picking && (
        <div style={{
          display: "flex", flexWrap: "wrap", gap: 6, maxWidth: 420,
          padding: "10px 12px", borderRadius: 14,
          background: "rgba(17,21,40,.92)",
          border: "1px solid var(--border-default)",
        }}>
          <span style={{ width: "100%", fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>
            어떤 점이 아쉬웠나요?
          </span>
          {REASONS.map(r => (
            <button
              key={r.code}
              onClick={() => send("dislike", r.code)}
              style={{
                fontSize: 11, padding: "5px 10px", borderRadius: 999,
                background: "rgba(139,124,255,.12)",
                border: "1px solid rgba(139,124,255,.3)",
                color: "var(--text-primary)", cursor: "pointer",
              }}
            >
              {r.label}
            </button>
          ))}
        </div>
      )}

      {sent === "dislike" && (
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>알려줘서 고마워요. 개선에 반영할게요</span>
      )}
    </div>
  );
}
