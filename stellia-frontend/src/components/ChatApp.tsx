import { useState, useEffect } from "react";
import axios from "axios";
import ChatHeader from "./ChatHeader";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import ProfilePanel from "./ProfilePanel";
import type { Character, Message, User } from "../App";

interface ChatAppProps {
  apiUrl: string;
  token: string;
  user: User | null;
  character: Character;
  onBack: () => void;
  onSelectCharacter?: (char: Character) => void;
}

const SESSION_ID = "session_" + Math.random().toString(36).substr(2, 9);

export default function ChatApp({ apiUrl, token, user, character, onBack, onSelectCharacter }: ChatAppProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [typing, setTyping] = useState(false);
  const [coins, setCoins] = useState<number>(user?.token_balance ?? 0);
  const [lowCoinAlert, setLowCoinAlert] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    // 대화 기록 불러오기
    axios.get(`${apiUrl}/chat/history/${character.id}`, { headers })
      .then(res => {
        const history: Message[] = res.data.map((m: any) => ({
          id: String(m.id || Math.random()),
          sender: m.role === "user" ? "user" : "ai",
          content: m.content,
          timestamp: new Date(m.created_at).toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        }));
        setMessages(history);
      })
      .catch(console.error);

    // 코인 조회
    refreshCoins();
  }, [character.id]);

  const refreshCoins = () => {
    axios.get(`${apiUrl}/tokens/me`, { headers })
      .then(res => {
        setCoins(res.data.token_balance);
        if (res.data.token_balance <= 100) setLowCoinAlert(true);
        else setLowCoinAlert(false);
      })
      .catch(console.error);
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages(prev => [...prev, userMessage]);
    setTyping(true);

    try {
      const res = await axios.post(
        `${apiUrl}/chat`,
        { character_id: character.id, message: text, session_id: SESSION_ID },
        { headers }
      );

      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          sender: "ai",
          content: res.data.message,
          timestamp: new Date().toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
      refreshCoins();

    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 400) {
        setLowCoinAlert(true);
        setMessages(prev => [
          ...prev,
          {
            id: crypto.randomUUID(),
            sender: "ai",
            content: "럭키 코인이 부족해요. 충전 후 다시 대화해요!",
            timestamp: new Date().toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            id: crypto.randomUUID(),
            sender: "ai",
            content: "오류가 발생했어요. 다시 시도해줘요.",
            timestamp: new Date().toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
      }
    } finally {
      setTyping(false);
    }
  };

  return (
    <div className="stellia-app">
      {/* 코인 부족 알림 */}
      {lowCoinAlert && (
        <div
          style={{
            position: "fixed",
            top: 20, left: "50%",
            transform: "translateX(-50%)",
            zIndex: 100,
            padding: "14px 24px",
            borderRadius: 16,
            background: "linear-gradient(135deg, rgba(246,198,91,.2), rgba(246,198,91,.1))",
            border: "1px solid rgba(246,198,91,.4)",
            color: "var(--gold)",
            fontWeight: 600, fontSize: 14,
            display: "flex", alignItems: "center", gap: 10,
            boxShadow: "0 0 30px rgba(246,198,91,.2)",
          }}
        >
          ✦ 럭키 코인이 부족해요! 충전이 필요해요.
          <button
            onClick={() => setLowCoinAlert(false)}
            style={{ background: "none", border: "none", color: "var(--gold)", cursor: "pointer", fontSize: 16 }}
          >
            ×
          </button>
        </div>
      )}

      {/* 뒤로가기 + 코인 표시 헤더 */}
      <div
        style={{
          position: "fixed",
          top: 0, left: 0,
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "12px 20px",
        }}
      >
        <button
          onClick={onBack}
          style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(9,11,20,.8)",
            color: "var(--text-primary)",
            fontSize: 18, cursor: "pointer",
            backdropFilter: "blur(12px)",
          }}
        >
          ←
        </button>
        <div style={{ color: "var(--gold)", fontWeight: 600, fontSize: 14 }}>
          ✦ {coins.toLocaleString()}
        </div>
      </div>

      <main
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          gridColumn: "1 / -1",
          background: "linear-gradient(to bottom, rgba(17,21,40,.45), rgba(9,11,20,.75))",
        }}
      >
        <ChatHeader
          character={character}
          apiUrl={apiUrl}
          token={token}
          sessionId={SESSION_ID}
          onBack={onBack}
          onSelectCharacter={onSelectCharacter}
        />

        <div
          style={{
            flex: 1, overflowY: "auto",
            padding: "28px",
            display: "flex", flexDirection: "column", gap: "18px",
          }}
        >
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              characterName={character.name}
            />
          ))}

          {typing && (
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div
                style={{
                  width: 42, height: 42, borderRadius: "50%",
                  background: "var(--gradient-cosmic)",
                  display: "grid", placeItems: "center",
                  fontWeight: 700, fontSize: 16, flexShrink: 0,
                }}
              >
                {character.name[0]}
              </div>
              <div className="glass-card" style={{ padding: "14px 18px", borderRadius: "999px", display: "flex", gap: "6px" }}>
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
        </div>

        <ChatInput onSend={handleSend} characterName={character.name} />
      </main>

      <ProfilePanel character={character} />

      <style>{`
        .typing-dot { width:8px; height:8px; border-radius:50%; background:var(--primary); animation:pulse 1.2s infinite; }
        .typing-dot:nth-child(2) { animation-delay:.15s; }
        .typing-dot:nth-child(3) { animation-delay:.3s; }
        @keyframes pulse { 0%,100%{opacity:.4;transform:translateY(0)} 50%{opacity:1;transform:translateY(-3px)} }
      `}</style>
    </div>
  );
}