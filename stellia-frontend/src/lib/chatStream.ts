/**
 * SSE 채팅 스트림 클라이언트.
 *
 * EventSource 는 POST 를 못 보내므로 fetch + ReadableStream 으로 직접 파싱한다.
 * 서버 이벤트: delta(조각) / done(저장 결과) / error
 */
export interface StreamDone {
  message_id: number | null;
  emotion: string;
  situation: string;
  character?: string;
}

export interface StreamHandlers {
  onDelta: (text: string) => void;
  onDone: (done: StreamDone) => void;
  onError: (detail: string, refunded?: number) => void;
}

export async function streamChat(
  apiUrl: string,
  token: string,
  body: { character_id: string; message: string; session_id: string },
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${apiUrl}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
    signal,
  });

  // 스트림 시작 전 오류(402 토큰부족, 403 권한 등)는 일반 JSON 으로 온다
  if (!res.ok || !res.body) {
    let detail = "대화에 실패했어요.";
    try {
      const j = await res.json();
      if (j?.detail) detail = j.detail;
    } catch {
      /* 본문이 JSON 이 아닐 수 있다 */
    }
    handlers.onError(detail);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flushEvent = (raw: string) => {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (!dataLines.length) return;
    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(dataLines.join("\n"));
    } catch {
      return;
    }
    if (event === "delta") handlers.onDelta(String(payload.text ?? ""));
    else if (event === "done") handlers.onDone(payload as unknown as StreamDone);
    else if (event === "error") {
      handlers.onError(
        String(payload.detail ?? "오류가 발생했어요."),
        payload.refunded as number | undefined,
      );
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 이벤트는 빈 줄로 구분된다
    let sep = buffer.indexOf("\n\n");
    while (sep !== -1) {
      flushEvent(buffer.slice(0, sep));
      buffer = buffer.slice(sep + 2);
      sep = buffer.indexOf("\n\n");
    }
  }
  if (buffer.trim()) flushEvent(buffer);
}
