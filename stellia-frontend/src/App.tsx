import { useState, useEffect } from "react";
import axios from "axios";
import StarBackground from "./components/StarBackground";
import LoginPage from "./components/LoginPage";
import HomePage from "./components/HomePage";
import ChatApp from "./components/ChatApp";
import PartyLobbyPage from "./components/PartyLobbyPage";
import PartyRoomPage from "./components/PartyRoomPage";
import PartyChatPage from "./components/PartyChatPage";
import CreateCharacterPage from "./components/CreateCharacterPage";
import TermsPage from "./components/TermsPage";
import PrivacyPage from "./components/PrivacyPage";
import LoginPromptModal from "./components/LoginPromptModal";
import EventsPage from "./components/EventsPage";
import MyPage from "./components/MyPage";
import AdminPage from "./components/AdminPage";
import CharacterProfileModal from "./components/CharacterProfileModal";

export interface Character {
  id: string;
  name: string;
  title: string;
  avatar: string;
  description: string;
  online: boolean;
  tags: string[];
  user_id?: number;
  first_message?: string;
}

export interface Message {
  id: string;
  sender: "user" | "ai";
  content: string;
  timestamp: string;
}

export interface User {
  id: number;
  username: string;
  token_balance: number;
  email?: string;
  safety_mode?: number;
  output_length?: string;
}

const API_URL = "http://localhost:8000";

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<"home" | "chat" | "party-lobby" | "party-room" | "party-chat" | "create" | "terms" | "privacy" | "login" | "events" | "mypage" | "admin">("home");
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [partyRoomCode, setPartyRoomCode] = useState<string>("");
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [sharedCharacter, setSharedCharacter] = useState<Character | null>(null);

  // 공유 링크 처리
  useEffect(() => {
    const hash = window.location.hash;
    const match = hash.match(/^#\/characters\/(.+)$/);
    if (match) {
      const characterId = match[1];
      axios.get(`${API_URL}/characters/${characterId}`)
        .then(res => {
          const c = res.data;
          setSharedCharacter({
            id: c.id,
            name: c.name,
            title: c.description || "",
            avatar: c.image_url || "",
            description: c.description || "",
            online: true,
            tags: c.tags || [],
            user_id: c.user_id,
            first_message: c.first_message || "",
          });
        })
        .catch(console.error);
    }
  }, []);

  const handleLogin = (accessToken: string, userData: User) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    setUser(userData);
    setView("home");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setUser(null);
    setView("home");
    setSelectedCharacter(null);
    setPartyRoomCode("");
  };

  const handleSelectCharacter = (char: Character) => {
    setSelectedCharacter(char);
    setView("chat");
  };

  const handleEnterParty = (roomCode: string) => {
    setPartyRoomCode(roomCode);
    setView("party-room");
  };

  const handleStartPartyChat = (roomCode: string) => {
    setPartyRoomCode(roomCode);
    setView("party-chat");
  };

  return (
    <>
      <StarBackground />

      {/* 공유 링크로 접근 시 캐릭터 프로필 모달 */}
      {sharedCharacter && (
        <CharacterProfileModal
          character={sharedCharacter}
          apiUrl={API_URL}
          token={token ?? ""}
          onClose={() => {
            setSharedCharacter(null);
            window.location.hash = "";
          }}
        />
      )}

      {showLoginPrompt && (
        <LoginPromptModal
          onClose={() => setShowLoginPrompt(false)}
          onLogin={() => { setShowLoginPrompt(false); setView("login"); }}
          onRegister={() => { setShowLoginPrompt(false); setView("login"); }}
        />
      )}

      {view === "terms" ? (
        <TermsPage onBack={() => setView("home")} />
      ) : view === "privacy" ? (
        <PrivacyPage onBack={() => setView("home")} />
      ) : view === "events" ? (
        <EventsPage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("home")}
        />
      ) : view === "mypage" ? (
        <MyPage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("home")}
          onGoAdmin={() => setView("admin")}
        />
      ) : view === "admin" ? (
        <AdminPage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("mypage")}
        />
      ) : !token ? (
        <>
          {view === "login" ? (
            <LoginPage
              apiUrl={API_URL}
              onLogin={handleLogin}
              onShowTerms={() => setView("terms")}
              onShowPrivacy={() => setView("privacy")}
            />
          ) : (
            <HomePage
              apiUrl={API_URL}
              token=""
              user={null}
              onSelectCharacter={() => setShowLoginPrompt(true)}
              onLogout={() => setView("login")}
              onGoParty={() => setShowLoginPrompt(true)}
              onCreateCharacter={() => setShowLoginPrompt(true)}
              onGoEvents={() => setShowLoginPrompt(true)}
              onGoMyPage={() => setShowLoginPrompt(true)}
            />
          )}
        </>
      ) : view === "home" ? (
        <HomePage
          apiUrl={API_URL}
          token={token}
          user={user}
          onSelectCharacter={handleSelectCharacter}
          onLogout={handleLogout}
          onGoParty={() => setView("party-lobby")}
          onCreateCharacter={() => setView("create")}
          onGoEvents={() => setView("events")}
          onGoMyPage={() => setView("mypage")}
        />
      ) : view === "chat" ? (
        <ChatApp
          apiUrl={API_URL}
          token={token}
          user={user}
          character={selectedCharacter!}
          onBack={() => setView("home")}
          onSelectCharacter={handleSelectCharacter}
        />
      ) : view === "create" ? (
        <CreateCharacterPage
          apiUrl={API_URL}
          token={token}
          onBack={() => setView("home")}
          onCreated={() => setView("home")}
        />
      ) : view === "party-lobby" ? (
        <PartyLobbyPage
          apiUrl={API_URL}
          token={token}
          user={user}
          onBack={() => setView("home")}
          onEnterRoom={handleEnterParty}
        />
      ) : view === "party-room" ? (
        <PartyRoomPage
          apiUrl={API_URL}
          token={token}
          user={user}
          roomCode={partyRoomCode}
          onBack={() => setView("party-lobby")}
          onStartChat={handleStartPartyChat}
        />
      ) : view === "party-chat" ? (
        <PartyChatPage
          apiUrl={API_URL}
          token={token}
          user={user}
          roomCode={partyRoomCode}
          onBack={() => setView("party-room")}
          onLeave={() => setView("home")}
        />
      ) : null}
    </>
  );
}