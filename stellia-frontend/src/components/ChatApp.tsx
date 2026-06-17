import { useState, useEffect, useRef } from "react";
import axios from "axios";
import ChatHeader from "./ChatHeader";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import CharacterProfileModal from "./CharacterProfileModal";
import ChatRoomModal from "./ChatRoomModal";
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
  const [showProfile, setShowProfile] = useState(false);
  const [showRoomModal, setShowRoomModal] = useState(false);
  const [showCharacterPanel, setShowCharacterPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/chat/history/${character.id}`, { headers })
      .then(res => {
        const history: Message[] = res.data
          .filter((m: any) => m.role !== "system")
          .map((m: any) => ({
            id: String(m.id || Math.random()),
            sender: m.role === "user" ? "user" : "ai",
            content: m.content,
            timestamp: new Date(m.created_at).toLocaleTimeString("ko-KR", {
              hour: "2-digit", minute: "2-digit",
            }),
          }));

        if (history.length === 0 && character.first_message) {
          setMessages([{
            id: crypto.randomUUID(),
            sender: "ai",
            content: character.first_message,
            timestamp: new Date().toLocaleTimeString("ko-KR", {
              hour: "2-digit", minute: "2-digit",
            }),
          }]);
        } else {
          setMessages(history);
        }
      })
      .catch(console.error);

    refreshCoins();
  }, [character.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const refreshCoins = () => {
    axios.get(`${apiUrl}/tokens/me`, { headers })
      .then(res => {
        setCoins(res.data.token_balance);
        if (res.data.token_balance <= 100) setLowCoinAlert(true);
        else setLowCoinAlert(false);
      })
      .catch(console.error);
  };

  const handleExportPdf = async () => {
    try {
      const res = await axios.get(
        `${apiUrl}/chat/export/${character.id}?session_id=${SESSION_ID}`,
        { headers, responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${character.name}_대화.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("PDF 내보내기에 실패했어요.");
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString("ko-KR", {
        hour: "2-digit", minute: "2-digit",
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
            hour: "2-digit", minute: "2-digit",
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
              hour: "2-digit", minute: "2-digit",
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
              hour: "2-digit", minute: "2-digit",
            }),
          },
        ]);
      }
    } finally {
      setTyping(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", position: "relative", zIndex: 2 }}>
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

      {/* 채팅 메인 영역 */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          background: "linear-gradient(to bottom, rgba(17,21,40,.45), rgba(9,11,20,.75))",
          borderRight: showCharacterPanel ? "1px solid var(--border-subtle)" : "none",
        }}
      >
        <ChatHeader
          character={character}
          apiUrl={apiUrl}
          token={token}
          sessionId={SESSION_ID}
          onBack={onBack}
          onSelectCharacter={onSelectCharacter}
          onShowProfile={() => setShowProfile(true)}
          onShowRoomModal={() => setShowRoomModal(true)}
          onTogglePanel={() => setShowCharacterPanel(prev => !prev)}
          showPanel={showCharacterPanel}
          coins={coins}
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
          <div ref={messagesEndRef} />
        </div>

        <ChatInput onSend={handleSend} characterName={character.name} />
      </main>

      {/* 오른쪽 캐릭터 이미지 패널 */}
      {showCharacterPanel && (
        <aside
          style={{
            width: 280, flexShrink: 0,
            height: "100vh",
            background: "rgba(9,11,20,.95)",
            backdropFilter: "blur(20px)",
            display: "flex", flexDirection: "column",
            alignItems: "center",
            padding: 24, gap: 16,
            overflowY: "auto",
          }}
        >
          {character.avatar ? (
            <img
              src={character.avatar}
              alt={character.name}
              style={{
                width: "100%", borderRadius: 20,
                objectFit: "cover",
                boxShadow: "0 0 40px rgba(139,124,255,.2)",
              }}
            />
          ) : (
            <div
              style={{
                width: "100%", aspectRatio: "3/4",
                borderRadius: 20,
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontSize: 80, fontWeight: 700,
              }}
            >
              {character.name[0]}
            </div>
          )}
          <div style={{ fontWeight: 700, fontSize: 18, textAlign: "center" }}>{character.name}</div>
          {character.description && (
            <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6, textAlign: "center" }}>
              {character.description}
            </div>
          )}
        </aside>
      )}

      {/* 캐릭터 프로필 모달 */}
      {showProfile && (
        <CharacterProfileModal
          character={character}
          apiUrl={apiUrl}
          token={token}
          onClose={() => setShowProfile(false)}
        />
      )}

      {/* 채팅방 관리 모달 */}
      {showRoomModal && (
        <ChatRoomModal
          apiUrl={apiUrl}
          token={token}
          characterId={character.id}
          sessionId={SESSION_ID}
          onClose={() => setShowRoomModal(false)}
          onExportPdf={handleExportPdf}
        />
      )}

      <style>{`
        .typing-dot { width:8px; height:8px; border-radius:50%; background:var(--primary); animation:pulse 1.2s infinite; }
        .typing-dot:nth-child(2) { animation-delay:.15s; }
        .typing-dot:nth-child(3) { animation-delay:.3s; }
        @keyframes pulse { 0%,100%{opacity:.4;transform:translateY(0)} 50%{opacity:1;transform:translateY(-3px)} }
      `}</style>
    </div>
  );
}