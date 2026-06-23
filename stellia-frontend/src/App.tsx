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
import EditCharacterPage from "./components/EditCharacterPage";
import CreatorPage from "./components/CreatorPage";
import TermsPage from "./components/TermsPage";
import PrivacyPage from "./components/PrivacyPage";
import LoginPromptModal from "./components/LoginPromptModal";
import EventsPage from "./components/EventsPage";
import MyPage from "./components/MyPage";
import AdminPage from "./components/AdminPage";
import CharacterProfileModal from "./components/CharacterProfileModal";
import RankingPage from "./components/RankingPage";
import NoticePage from "./components/NoticePage";

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
  party_enabled?: boolean;
  like_count?: number;
  chat_count?: number;
  view_count?: number;
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
  profile_image_url?: string;
  is_admin?: number;
}

const API_URL = "https://suburb-marrow-radial.ngrok-free.dev";

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<"home" | "chat" | "party-lobby" | "party-room" | "party-chat" | "create" | "edit-character" | "creator" | "terms" | "privacy" | "login" | "events" | "mypage" | "ranking" | "notice" | "admin">("home");
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [partyRoomCode, setPartyRoomCode] = useState<string>("");
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [sharedCharacter, setSharedCharacter] = useState<Character | null>(null);
  const [editCharacterId, setEditCharacterId] = useState<string | null>(null);
  const [creatorUserId, setCreatorUserId] = useState<number | null>(null);
  

  useEffect(() => {
    if (token) {
      axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(res => setUser(res.data)).catch(() => {
        localStorage.removeItem("access_token");
        setToken(null);
      });
    }
  }, []);

  useEffect(() => {
    const hash = window.location.hash;
    const match = hash.match(/^#\/characters\/(.+)$/);
    if (match) {
      const characterId = match[1];
      axios.get(`${API_URL}/characters/${characterId}`)
        .then(res => {
          const c = res.data;
          setSharedCharacter({
            id: c.id, name: c.name,
            title: c.description || "",
            avatar: c.image_url || "",
            description: c.description || "",
            online: true, tags: c.tags || [],
            user_id: c.user_id,
            first_message: c.first_message || "",
            party_enabled: c.party_enabled || false,
            like_count: c.like_count ?? 0,
            chat_count: c.chat_count ?? 0,
            view_count: c.view_count ?? 0,
          });
        })
        .catch(console.error);
    }
  }, []);

  const handleLogin = (accessToken: string, userData: User) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` }
    }).then(res => setUser(res.data)).catch(() => setUser(userData));
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

  const handleGoCreator = (userId: number) => {
    setCreatorUserId(userId);
    setView("creator");
  };

  return (
    <>
      <StarBackground />

      {/* 공유 캐릭터 모달 */}
      {sharedCharacter && (
        <CharacterProfileModal
          character={sharedCharacter}
          apiUrl={API_URL}
          token={token ?? ""}
          onClose={() => { setSharedCharacter(null); window.location.hash = ""; }}
          onGoParty={(code) => { setPartyRoomCode(code); setView("party-room"); }}
          onGoCreator={handleGoCreator}
        />
      )}

      {/* 로그인 유도 모달 */}
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
      ) : view === "ranking" ? (
        <RankingPage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("home")}
          onSelectCharacter={handleSelectCharacter}
        />
      ) : view === "mypage" ? (
        <MyPage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("home")}
          onGoAdmin={() => setView("admin")}
          onEditCharacter={(id) => { setEditCharacterId(id); setView("edit-character"); }}
        />
      ) : view === "edit-character" ? (
        <EditCharacterPage
          apiUrl={API_URL}
          token={token ?? ""}
          characterId={editCharacterId ?? ""}
          onBack={() => setView("mypage")}
          onSaved={() => setView("mypage")}
        />
      ) : view === "creator" ? (
        <CreatorPage
          apiUrl={API_URL}
          token={token ?? ""}
          userId={creatorUserId ?? 0}
          onBack={() => setView("home")}
          onSelectCharacter={handleSelectCharacter}
        />
      ) : view === "admin" ? (
        <AdminPage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("mypage")}
        />
      ) : view === "notice" ? (
        <NoticePage
          apiUrl={API_URL}
          token={token ?? ""}
          onBack={() => setView("home")}
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
              onGoRanking={() => setView("ranking")}
              onGoNotice={() => setView("notice")}
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
          onGoRanking={() => setView("ranking")}
          onGoNotice={() => setView("notice")}
        />
      ) : view === "chat" ? (
        <ChatApp
          apiUrl={API_URL}
          token={token}
          user={user}
          character={selectedCharacter!}
          onBack={() => setView("home")}
          onSelectCharacter={handleSelectCharacter}
          onGoCreator={handleGoCreator}
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