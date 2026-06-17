import { useState, useEffect, useRef } from "react";
import type { User } from "../App";

interface PartyChatPageProps {
  apiUrl: string;
  token: string;
  user: User | null;
  roomCode: string;
  onBack: () => void;
  onLeave: () => void;
}

interface PartyMessage {
  type: "chat" | "narration" | "system" | "kick_vote_started" | "kick_vote_update" | "kick_result" | "host_delegated" | "settings_updated" | "kicked";
  username?: string;
  message: string;
  target_user_id?: number;
  target_username?: string;
  proposer_id?: number;
  new_host_id?: number;
  new_host_username?: string;
  output_multiplier?: number;
}

export default function PartyChatPage({ apiUrl, token, user, roomCode, onBack, onLeave }: PartyChatPageProps) {
  const [messages, setMessages] = useState<PartyMessage[]>([]);
  const [input, setInput] = useState("");
  const [members, setMembers] = useState<string[]>([]);
  const [_, setHostId] = useState<number | null>(null);
  const [room, setRoom] = useState<any>(null);
  const [started, setStarted] = useState(false);
  const [kickVotes, setKickVotes] = useState<Record<number, { yes: number; no: number; total: number }>>({});
  const [connected, setConnected] = useState(false);
  const [showLog, setShowLog] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const wsUrl = apiUrl.replace("http", "ws");

  useEffect(() => {
    // 방 정보 먼저 로드
    fetch(`${apiUrl}/party/rooms/${roomCode}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => res.json())
      .then(data => {
        setRoom(data.room);
        setHostId(data.room.host_id);
        setMembers(data.members.map((m: any) => m.username));
      });

    // WebSocket 연결
    const ws = new WebSocket(`${wsUrl}/party/ws/${roomCode}/${user?.id}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data: PartyMessage = JSON.parse(event.data);

      if (data.type === "kicked") {
        alert("투표로 강퇴되었습니다.");
        onLeave();
        return;
      }

      if (data.type === "host_delegated" && data.new_host_id) {
        setHostId(data.new_host_id);
      }

      if (data.type === "kick_vote_update") {
        const payload = data as any;
        setKickVotes(prev => ({
          ...prev,
          [payload.target_user_id]: {
            yes: payload.yes,
            no: payload.no,
            total: payload.total_members,
          },
        }));
      }

      if (data.type === "system") {
        const payload = data as any;
        if (payload.members) setMembers(payload.members);
      }

      setMessages(prev => [...prev, data]);
    };

    ws.onclose = () => setConnected(false);

    return () => ws.close();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = (type: string, extra?: object) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type, message: input, ...extra }));
  };

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage("chat");
    setInput("");
  };

  const handleStart = () => {
    sendMessage("start", { message: "스토리 시작" });
    setStarted(true);
  };

  const handleKickVote = (targetUserId: number) => {
    sendMessage("kick_vote", { message: "", target_user_id: targetUserId });
  };

  const handleVote = (targetUserId: number, vote: "yes" | "no") => {
    sendMessage("kick_vote_result", { message: "", target_user_id: targetUserId, vote });
  };

  const handleExportLog = async () => {
    const res = await fetch(`${apiUrl}/party/rooms/${roomCode}/log/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `party_log_${roomCode}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const isHost = room?.host_id === user?.id;

  const renderMessage = (msg: PartyMessage, idx: number) => {
    if (msg.type === "system" || msg.type === "host_delegated" || msg.type === "settings_updated") {
      return (
        <div key={idx} style={{ textAlign: "center", color: "var(--text-muted)", fontSize: 13, padding: "8px 0" }}>
          {msg.message}
        </div>
      );
    }

    if (msg.type === "narration") {
      return (
        <div
          key={idx}
          style={{
            padding: "16px 20px", borderRadius: 16, margin: "8px 0",
            background: "linear-gradient(135deg, rgba(139,124,255,.15), rgba(95,214,255,.08))",
            border: "1px solid rgba(139,124,255,.2)",
            color: "var(--text-primary)", lineHeight: 1.8, fontSize: 15,
            fontStyle: "italic",
          }}
        >
          <div style={{ color: "var(--primary)", fontSize: 12, marginBottom: 8, fontStyle: "normal" }}>📖 나레이션</div>
          {msg.message}
        </div>
      );
    }

    if (msg.type === "kick_vote_started") {
      return (
        <div
          key={idx}
          style={{
            padding: 16, borderRadius: 16, margin: "8px 0",
            background: "rgba(255,107,138,.08)",
            border: "1px solid rgba(255,107,138,.2)",
          }}
        >
          <div style={{ color: "#ff6b8a", fontWeight: 600, marginBottom: 12 }}>
            ⚠ {msg.message}
          </div>
          {kickVotes[msg.target_user_id!] && (
            <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 10 }}>
              찬성 {kickVotes[msg.target_user_id!].yes} / 반대 {kickVotes[msg.target_user_id!].no}
            </div>
          )}
          {msg.target_user_id !== user?.id && (
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => handleVote(msg.target_user_id!, "yes")}
                style={{
                  flex: 1, padding: "8px", borderRadius: 10, border: "none",
                  background: "rgba(255,107,138,.2)", color: "#ff6b8a",
                  fontWeight: 600, cursor: "pointer",
                }}
              >
                찬성
              </button>
              <button
                onClick={() => handleVote(msg.target_user_id!, "no")}
                style={{
                  flex: 1, padding: "8px", borderRadius: 10,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)", color: "var(--text-muted)",
                  fontWeight: 600, cursor: "pointer",
                }}
              >
                반대
              </button>
            </div>
          )}
        </div>
      );
    }

    if (msg.type === "kick_result") {
      return (
        <div key={idx} style={{ textAlign: "center", color: "#ff6b8a", fontSize: 13, padding: "8px 0" }}>
          {msg.message}
        </div>
      );
    }

    // 일반 채팅
    const isMe = msg.username === user?.username;
    return (
      <div key={idx} style={{ display: "flex", justifyContent: isMe ? "flex-end" : "flex-start", marginBottom: 8 }}>
        {!isMe && (
          <div
            style={{
              width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
              background: "var(--gradient-cosmic)",
              display: "grid", placeItems: "center",
              fontWeight: 700, fontSize: 13, marginRight: 8,
            }}
          >
            {msg.username?.[0]?.toUpperCase()}
          </div>
        )}
        <div style={{ maxWidth: "70%" }}>
          {!isMe && (
            <div style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 4 }}>{msg.username}</div>
          )}
          <div
            style={{
              padding: "12px 16px", borderRadius: isMe ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
              background: isMe
                ? "linear-gradient(135deg, var(--primary), var(--primary-active))"
                : "rgba(24,29,54,.95)",
              border: isMe ? "none" : "1px solid var(--border-default)",
              color: "#fff", fontSize: 15, lineHeight: 1.6,
            }}
          >
            {msg.message}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{ position: "relative", zIndex: 2, height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* 헤더 */}
      <div
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "0 24px", height: 72,
          background: "rgba(9,11,20,.85)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid var(--border-subtle)",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button
            onClick={onBack}
            style={{
              width: 38, height: 38, borderRadius: 10,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-primary)", fontSize: 16, cursor: "pointer",
            }}
          >
            ←
          </button>
          <div>
            <div style={{ fontWeight: 700 }}>{room?.story_id ? "파티챗" : "파티챗"}</div>
            <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
              {connected ? "🟢 연결됨" : "🔴 연결 중..."} · {members.length}명
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {/* 멤버 아바타 */}
          <div style={{ display: "flex", gap: -4 }}>
            {members.map((m, i) => (
              <div
                key={i}
                title={m}
                style={{
                  width: 30, height: 30, borderRadius: "50%",
                  background: "var(--gradient-cosmic)",
                  display: "grid", placeItems: "center",
                  fontWeight: 700, fontSize: 12,
                  border: "2px solid var(--bg-base)",
                  marginLeft: i > 0 ? -8 : 0,
                }}
              >
                {m[0]?.toUpperCase()}
              </div>
            ))}
          </div>

          {/* 로그 보기 */}
          <button
            onClick={() => setShowLog(!showLog)}
            style={{
              padding: "6px 12px", borderRadius: 8, fontSize: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", cursor: "pointer",
            }}
          >
            📋 로그
          </button>

          {/* PDF 내보내기 */}
          <button
            onClick={handleExportLog}
            style={{
              padding: "6px 12px", borderRadius: 8, fontSize: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", cursor: "pointer",
            }}
          >
            📄 저장
          </button>

          {/* 나가기 */}
          <button
            onClick={onLeave}
            style={{
              padding: "6px 12px", borderRadius: 8, fontSize: 12,
              border: "1px solid rgba(255,107,138,.3)",
              background: "rgba(255,107,138,.08)",
              color: "#ff6b8a", cursor: "pointer",
            }}
          >
            나가기
          </button>
        </div>
      </div>

      {/* 채팅 영역 */}
      <div
        style={{
          flex: 1, overflowY: "auto",
          padding: "20px 24px",
          display: "flex", flexDirection: "column",
        }}
      >
        {!started && isHost && (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <div style={{ color: "var(--text-muted)", fontSize: 15, marginBottom: 20 }}>
              모든 멤버가 준비됐으면 스토리를 시작하세요.
            </div>
            <button
              onClick={handleStart}
              style={{
                padding: "16px 40px", borderRadius: 16, border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 700, fontSize: 16,
                cursor: "pointer",
                boxShadow: "0 0 30px rgba(139,124,255,.3)",
              }}
            >
              ⚔ 스토리 시작
            </button>
          </div>
        )}

        {!started && !isHost && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
            방장이 스토리를 시작하기를 기다리는 중...
          </div>
        )}

        {messages.map((msg, idx) => renderMessage(msg, idx))}
        <div ref={messagesEndRef} />
      </div>

      {/* 강퇴 투표 버튼 (멤버 목록) */}
      {started && members.length > 2 && (
        <div
          style={{
            padding: "8px 24px",
            borderTop: "1px solid var(--border-subtle)",
            display: "flex", gap: 8, overflowX: "auto",
          }}
        >
          {members.filter(m => m !== user?.username).map((m, i) => (
            <button
              key={i}
              onClick={() => {
                const targetId = room?.members?.find((mem: any) => mem.username === m)?.user_id;
                if (targetId) handleKickVote(targetId);
              }}
              style={{
                padding: "4px 10px", borderRadius: 8, fontSize: 11,
                border: "1px solid rgba(255,107,138,.2)",
                background: "rgba(255,107,138,.06)",
                color: "#ff6b8a", cursor: "pointer", whiteSpace: "nowrap",
              }}
            >
              {m} 강퇴 투표
            </button>
          ))}
        </div>
      )}

      {/* 입력창 */}
      {started && (
        <div
          style={{
            padding: "16px 24px",
            borderTop: "1px solid var(--border-subtle)",
            background: "rgba(9,11,20,.8)",
            backdropFilter: "blur(20px)",
          }}
        >
          <div
            style={{
              display: "flex", gap: 12, alignItems: "center",
              padding: "10px 16px", borderRadius: 18,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
            }}
          >
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              placeholder="메시지를 입력하세요..."
              style={{
                flex: 1, border: "none", outline: "none",
                background: "transparent",
                color: "var(--text-primary)", fontSize: 15,
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              style={{
                width: 40, height: 40, borderRadius: 12, border: "none",
                background: input.trim() ? "var(--gradient-cosmic)" : "rgba(255,255,255,.06)",
                color: "#fff", cursor: input.trim() ? "pointer" : "not-allowed",
                fontSize: 16,
              }}
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  );
}