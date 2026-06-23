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
  onGoCreator?: (userId: number) => void;
}

export default function ChatApp({ apiUrl, token, user, character, onBack, onSelectCharacter, onGoCreator }: ChatAppProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [typing, setTyping] = useState(false);
  const [coins, setCoins] = useState<number>(user?.token_balance ?? 0);
  const [lowCoinAlert, setLowCoinAlert] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showRoomModal, setShowRoomModal] = useState(false);
  const [showCharacterPanel, setShowCharacterPanel] = useState(false);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState("neutral");
  const [currentSituation, setCurrentSituation] = useState("default");
  const [emotionImages, setEmotionImages] = useState<Record<string, string>>({});
  const [backgroundImages, setBackgroundImages] = useState<Record<string, string>>({});
  const [sessionId, setSessionId] = useState<string>("");
  const [sessions, setSessions] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const headers = { Authorization: `Bearer ${token}` };

  // 세션 초기화: 가장 최근 세션 불러오거나 새 세션 생성
  useEffect(() => {
    const initSession = async () => {
      if (!token) {
        const newId = "session_" + Math.random().toString(36).substr(2, 9);
        setSessionId(newId);
        if (character.first_message) {
          setMessages([{
            id: crypto.randomUUID(),
            sender: "ai",
            content: character.first_message,
            timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
          }]);
        }
        return;
      }

      try {
        const res = await axios.get(`${apiUrl}/chat/sessions/${character.id}`, { headers });
        const sessionList = res.data;
        setSessions(sessionList);

        if (sessionList.length > 0) {
          // 가장 최근 세션 이어하기
          const latestSession = sessionList[0].session_id;
          setSessionId(latestSession);
          loadHistory();
        } else {
          // 새 세션
          const newId = "session_" + Math.random().toString(36).substr(2, 9);
          setSessionId(newId);
          if (character.first_message) {
            setMessages([{
              id: crypto.randomUUID(),
              sender: "ai",
              content: character.first_message,
              timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
            }]);
          }
        }
      } catch {
        const newId = "session_" + Math.random().toString(36).substr(2, 9);
        setSessionId(newId);
      }
    };

    initSession();
    refreshCoins();

    axios.get(`${apiUrl}/characters/${character.id}/emotions`, { headers })
      .then(res => setEmotionImages(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/characters/${character.id}/backgrounds`, { headers })
      .then(res => setBackgroundImages(res.data))
      .catch(console.error);
  }, [character.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const res = await axios.get(`${apiUrl}/chat/history/${character.id}`, { headers });
      const history: Message[] = res.data
        .filter((m: any) => m.role !== "system")
        .map((m: any) => ({
          id: String(m.id || Math.random()),
          sender: m.role === "user" ? "user" : "ai",
          content: m.content,
          timestamp: new Date(m.created_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        }));

      if (history.length === 0 && character.first_message) {
        setMessages([{
          id: crypto.randomUUID(),
          sender: "ai",
          content: character.first_message,
          timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        }]);
      } else {
        setMessages(history);
      }
    } catch {
      console.error("히스토리 로드 실패");
    }
  };

  const handleNewSession = () => {
    const newId = "session_" + Math.random().toString(36).substr(2, 9);
    setSessionId(newId);
    setMessages([]);
    if (character.first_message) {
      setMessages([{
        id: crypto.randomUUID(),
        sender: "ai",
        content: character.first_message,
        timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
      }]);
    }
    setShowSessionModal(false);
  };

  const handleSelectSession = async (sid: string) => {
    setSessionId(sid);
    setShowSessionModal(false);
    try {
      const res = await axios.get(
        `${apiUrl}/chat/resume/${character.id}?session_id=${sid}`,
        { headers }
      );
      const history: Message[] = res.data.history
        .filter((m: any) => m.role !== "system")
        .map((m: any) => ({
          id: String(m.id || Math.random()),
          sender: m.role === "user" ? "user" : "ai",
          content: m.content,
          timestamp: new Date(m.created_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        }));
      setMessages(history);
    } catch {
      console.error("세션 복원 실패");
    }
  };

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
        `${apiUrl}/chat/export/${character.id}?session_id=${sessionId}`,
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
    if (!text.trim() || !sessionId) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages(prev => [...prev, userMessage]);
    setTyping(true);

    try {
      const res = await axios.post(
        `${apiUrl}/chat`,
        { character_id: character.id, message: text, session_id: sessionId },
        { headers }
      );

      if (res.data.emotion) setCurrentEmotion(res.data.emotion);
      if (res.data.situation) setCurrentSituation(res.data.situation);

      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        sender: "ai",
        content: res.data.message,
        timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
      }]);
      refreshCoins();

    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 400) {
        setLowCoinAlert(true);
        setMessages(prev => [...prev, {
          id: crypto.randomUUID(),
          sender: "ai",
          content: "럭키 코인이 부족해요. 충전 후 다시 대화해요!",
          timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: crypto.randomUUID(),
          sender: "ai",
          content: "오류가 발생했어요. 다시 시도해줘요.",
          timestamp: new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }),
        }]);
      }
    } finally {
      setTyping(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", position: "relative", zIndex: 2 }}>

      {/* 코인 부족 알림 */}
      {lowCoinAlert && (
        <div style={{
          position: "fixed", top: 20, left: "50%",
          transform: "translateX(-50%)", zIndex: 100,
          padding: "14px 24px", borderRadius: 16,
          background: "linear-gradient(135deg, rgba(246,198,91,.2), rgba(246,198,91,.1))",
          border: "1px solid rgba(246,198,91,.4)",
          color: "var(--gold)", fontWeight: 600, fontSize: 14,
          display: "flex", alignItems: "center", gap: 10,
          boxShadow: "0 0 30px rgba(246,198,91,.2)",
        }}>
          ✦ 럭키 코인이 부족해요! 충전이 필요해요.
          <button onClick={() => setLowCoinAlert(false)}
            style={{ background: "none", border: "none", color: "var(--gold)", cursor: "pointer", fontSize: 16 }}>×</button>
        </div>
      )}

      {/* 채팅 메인 */}
      <main style={{
        flex: 1, display: "flex", flexDirection: "column",
        height: "100vh", position: "relative", overflow: "hidden",
        borderRight: showCharacterPanel ? "1px solid var(--border-subtle)" : "none",
      }}>
        {/* 배경 */}
        {backgroundImages[currentSituation] ? (
          <div style={{
            position: "absolute", inset: 0, zIndex: 0,
            backgroundImage: `url(${backgroundImages[currentSituation]})`,
            backgroundSize: "cover", backgroundPosition: "center",
            opacity: 0.3, transition: "all 0.5s ease",
          }} />
        ) : (
          <div style={{
            position: "absolute", inset: 0, zIndex: 0,
            background: "linear-gradient(to bottom, rgba(17,21,40,.45), rgba(9,11,20,.75))",
          }} />
        )}

        {/* 헤더 */}
        <div style={{ position: "relative", zIndex: 3 }}>
          <ChatHeader
            character={character}
            apiUrl={apiUrl}
            token={token}
            sessionId={sessionId}
            onBack={onBack}
            onSelectCharacter={onSelectCharacter}
            onShowProfile={() => setShowProfile(true)}
            onShowRoomModal={() => setShowRoomModal(true)}
            onTogglePanel={() => setShowCharacterPanel(prev => !prev)}
            showPanel={showCharacterPanel}
            coins={coins}
          />
        </div>

        {/* 세션 선택 버튼 */}
        {token && sessions.length > 0 && (
          <div style={{
            position: "relative", zIndex: 3,
            padding: "8px 20px",
            borderBottom: "1px solid var(--border-subtle)",
            background: "rgba(9,11,20,.6)",
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <button onClick={() => setShowSessionModal(true)} style={{
              padding: "6px 14px", borderRadius: 999, fontSize: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", cursor: "pointer",
            }}>📂 대화 목록</button>
            <button onClick={handleNewSession} style={{
              padding: "6px 14px", borderRadius: 999, fontSize: 12,
              border: "1px solid rgba(139,124,255,.3)",
              background: "rgba(139,124,255,.08)",
              color: "var(--primary)", cursor: "pointer",
            }}>+ 새 대화</button>
            <span style={{ color: "var(--text-muted)", fontSize: 11 }}>
              세션: {sessionId.slice(-6)}
            </span>
          </div>
        )}

        {/* 메시지 영역 */}
        <div style={{
          flex: 1, overflowY: "auto",
          padding: "28px",
          display: "flex", flexDirection: "column", gap: "18px",
          position: "relative", zIndex: 1,
        }}>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} characterName={character.name} />
          ))}

          {typing && (
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div style={{
                width: 42, height: 42, borderRadius: "50%",
                background: "var(--gradient-cosmic)",
                display: "grid", placeItems: "center",
                fontWeight: 700, fontSize: 16, flexShrink: 0,
              }}>{character.name[0]}</div>
              <div className="glass-card" style={{ padding: "14px 18px", borderRadius: "999px", display: "flex", gap: "6px" }}>
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 입력창 */}
        <div style={{ position: "relative", zIndex: 3 }}>
          <ChatInput onSend={handleSend} characterName={character.name} />
        </div>
      </main>

      {/* 캐릭터 패널 */}
      {showCharacterPanel && (
        <aside style={{
          width: 280, flexShrink: 0, height: "100vh",
          background: "rgba(9,11,20,.95)",
          backdropFilter: "blur(20px)",
          display: "flex", flexDirection: "column",
          alignItems: "center", padding: 24, gap: 16, overflowY: "auto",
        }}>
          {(emotionImages[currentEmotion] || character.avatar) ? (
            <img src={emotionImages[currentEmotion] || character.avatar} alt={character.name}
              style={{ width: "100%", borderRadius: 20, objectFit: "cover", boxShadow: "0 0 40px rgba(139,124,255,.2)", transition: "opacity 0.3s ease" }} />
          ) : (
            <div style={{
              width: "100%", aspectRatio: "3/4", borderRadius: 20,
              background: "var(--gradient-cosmic)",
              display: "grid", placeItems: "center", fontSize: 80, fontWeight: 700,
            }}>{character.name[0]}</div>
          )}
          <div style={{ fontWeight: 700, fontSize: 18, textAlign: "center" }}>{character.name}</div>
          <div style={{
            padding: "4px 12px", borderRadius: 999,
            background: "rgba(139,124,255,.12)",
            border: "1px solid rgba(139,124,255,.2)",
            color: "var(--primary)", fontSize: 12,
          }}>{currentEmotion}</div>
          {character.description && (
            <div style={{ color: "var(--text-muted)", fontSize: 13, lineHeight: 1.6, textAlign: "center" }}>
              {character.description}
            </div>
          )}
        </aside>
      )}

      {/* 세션 목록 모달 */}
      {showSessionModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.7)", display: "grid", placeItems: "center", zIndex: 100 }}>
          <div style={{
            borderRadius: 24, padding: 28,
            background: "rgba(17,21,40,.98)",
            border: "1px solid var(--border-default)",
            width: 420, maxHeight: "70vh",
            display: "flex", flexDirection: "column", gap: 16,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontWeight: 700, fontSize: 18 }}>대화 목록</div>
              <button onClick={() => setShowSessionModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 22, cursor: "pointer" }}>×</button>
            </div>

            <button onClick={handleNewSession} style={{
              padding: "12px", borderRadius: 14, border: "none",
              background: "var(--gradient-cosmic)",
              color: "#fff", fontWeight: 700, cursor: "pointer",
            }}>+ 새 대화 시작</button>

            <div style={{ overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
              {sessions.map(s => (
                <div key={s.session_id}
                  onClick={() => handleSelectSession(s.session_id)}
                  style={{
                    padding: "14px 16px", borderRadius: 14,
                    border: s.session_id === sessionId ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                    background: s.session_id === sessionId ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.04)",
                    cursor: "pointer", transition: "all .2s ease",
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {s.session_id === sessionId ? "📂 현재 대화" : "💬 대화"}
                    </div>
                    <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
                      {s.message_count}개 메시지
                    </div>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                    시작: {new Date(s.started_at).toLocaleDateString("ko-KR")} ·
                    마지막: {new Date(s.last_at).toLocaleDateString("ko-KR")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 프로필 모달 */}
      {showProfile && (
        <CharacterProfileModal
          character={character}
          apiUrl={apiUrl}
          token={token}
          onClose={() => setShowProfile(false)}
          onGoCreator={onGoCreator}
        />
      )}

      {/* 채팅방 관리 모달 */}
      {showRoomModal && (
        <ChatRoomModal
          apiUrl={apiUrl}
          token={token}
          characterId={character.id}
          sessionId={sessionId}
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