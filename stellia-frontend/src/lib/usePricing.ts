import { useEffect, useState } from "react";
import axios from "axios";

/**
 * 요금표를 서버에서 받아온다.
 *
 * 설정 화면 3곳이 "300/1,000/2,000 토큰/회" 를 직접 박아두고 있었는데,
 * 그 숫자는 LLM 출력 토큰 상한이지 코인 요금이 아니었다. 실제 차감은
 * 세 옵션 모두 50코인이었고, 유저는 "길게 = 2,000코인" 으로 읽었다.
 */
export interface ChatPricing {
  value: string;
  label: string;
  desc: string;
  cost: number;
}

const FALLBACK: ChatPricing[] = [
  { value: "short", label: "짧게", desc: "간결하고 빠른 응답", cost: 30 },
  { value: "medium", label: "보통", desc: "적당한 길이의 응답", cost: 50 },
  { value: "long", label: "길게", desc: "상세하고 풍부한 응답", cost: 80 },
];

export function usePricing(apiUrl: string) {
  const [chat, setChat] = useState<ChatPricing[]>(FALLBACK);

  useEffect(() => {
    axios.get(`${apiUrl}/tokens/pricing`)
      .then(res => {
        if (Array.isArray(res.data?.chat) && res.data.chat.length) setChat(res.data.chat);
      })
      .catch(() => { /* 실패해도 기본값으로 표시 */ });
  }, [apiUrl]);

  return { chat };
}
