import { useState } from "react";
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

const API_URL = "";

export default function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("access_token")
  );
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<"home" | "chat" | "party-lobby" | "party-room" | "party-chat" | "create" | "terms" | "privacy" | "login">("home");
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [partyRoomCode, setPartyRoomCode] = useState<string>("");
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  

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