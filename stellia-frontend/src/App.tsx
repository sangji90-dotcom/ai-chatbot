import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useParams, Navigate, useSearchParams } from "react-router-dom";
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
import CommunityPage from "./components/CommunityPage";


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
  likes?: string;
  dislikes?: string;
  created_at?: string;
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

const API_URL = import.meta.env.VITE_API_URL;

// ── 인증 관련 전역 상태를 관리하는 Provider 역할 컴포넌트 ──────────
function AppRoutes() {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [user, setUser] = useState<User | null>(null);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [sharedCharacter, setSharedCharacter] = useState<Character | null>(null);
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [creatorUserId, setCreatorUserId] = useState<number | null>(null);
  const [profileModalChar, setProfileModalChar] = useState<Character | null>(null);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setUser(null);
    navigate("/");
  };

  const handleLogin = (accessToken: string, userData: User) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` }
    }).then(res => setUser(res.data)).catch(() => setUser(userData));
    navigate("/");
  };

  const handleSelectCharacter = (char: Character) => {
    setProfileModalChar(char);
  };

  const handleStartChat = (newSession: boolean) => {
    if (!profileModalChar) return;
    setSelectedCharacter(profileModalChar);
    navigate(`/chat/${profileModalChar.id}${newSession ? "?new=1" : ""}`);
    setProfileModalChar(null);
  };

  const handleGoCreator = (userId: number) => {
    setCreatorUserId(userId);
    navigate(`/creator/${userId}`);
  };

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
    const interceptor = axios.interceptors.response.use(
      res => res,
      async err => {
        const originalRequest = err.config;
        if (err.response?.status === 401 && !originalRequest._retry) {
          if (originalRequest.url?.includes('/auth/login') ||
              originalRequest.url?.includes('/auth/register')) {
            return Promise.reject(err);
          }
          originalRequest._retry = true;
          const refreshToken = localStorage.getItem("refresh_token");
          if (!refreshToken) {
            handleLogout();
            return Promise.reject(err);
          }
          try {
            const res = await axios.post(`${API_URL}/auth/refresh`, {
              refresh_token: refreshToken,
            });
            const newToken = res.data.access_token;
            localStorage.setItem("access_token", newToken);
            localStorage.setItem("refresh_token", res.data.refresh_token);
            setToken(newToken);
            originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
            return axios(originalRequest);
          } catch {
            handleLogout();
            return Promise.reject(err);
          }
        }
        return Promise.reject(err);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
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

  return (
    <>
      <StarBackground />

      {profileModalChar && (
        <CharacterProfileModal
        character={profileModalChar}
        apiUrl={API_URL}
        token={token ?? ""}
        onClose={() => setProfileModalChar(null)}
        onGoParty={(code) => { setProfileModalChar(null); navigate(`/party/room/${code}`); }}
        onGoCreator={handleGoCreator}
        onStartChat={handleStartChat}
      />
    )}

      {showLoginPrompt && (
        <LoginPromptModal
          onClose={() => setShowLoginPrompt(false)}
          onLogin={() => { setShowLoginPrompt(false); navigate("/login"); }}
          onRegister={() => { setShowLoginPrompt(false); navigate("/login"); }}
        />
      )}

      <Routes>
        <Route path="/terms" element={<TermsPage onBack={() => navigate("/")} />} />
        <Route path="/privacy" element={<PrivacyPage onBack={() => navigate("/")} />} />
        <Route path="/notice" element={<NoticePage apiUrl={API_URL} token={token ?? ""} onBack={() => navigate("/")} />} />

        <Route path="/events" element={
          token
            ? <EventsPage apiUrl={API_URL} token={token} onBack={() => navigate("/")} />
            : <Navigate to="/" replace />
        } />

        <Route path="/ranking" element={
          <RankingPage
            apiUrl={API_URL} token={token ?? ""}
            onBack={() => navigate("/")}
            onSelectCharacter={handleSelectCharacter}
          />
        } />

        <Route path="/mypage" element={
          token
            ? <MyPage
                apiUrl={API_URL} token={token}
                onBack={() => navigate("/")}
                onGoAdmin={() => navigate("/admin")}
                onEditCharacter={(id) => navigate(`/edit-character/${id}`)}
              />
            : <Navigate to="/" replace />
        } />

        <Route path="/edit-character/:id" element={
          <EditCharacterRoute apiUrl={API_URL} token={token} />
        } />

        <Route path="/creator/:userId" element={
          <CreatorRoute apiUrl={API_URL} token={token} onSelectCharacter={handleSelectCharacter} />
        } />

        <Route path="/admin" element={
          token
            ? <AdminPage apiUrl={API_URL} token={token} onBack={() => navigate("/mypage")} />
            : <Navigate to="/" replace />
        } />

        <Route path="/community" element={
          <CommunityPage
            apiUrl={API_URL} token={token ?? ""}
            user={user}
            onBack={() => navigate("/")}
            onSelectCharacter={handleSelectCharacter}
            onGoCreator={handleGoCreator}
            onLoginRequired={() => setShowLoginPrompt(true)}
          />
        } />

        <Route path="/login" element={
          token
            ? <Navigate to="/" replace />
            : <LoginPage
                apiUrl={API_URL}
                onLogin={handleLogin}
                onShowTerms={() => navigate("/terms")}
                onShowPrivacy={() => navigate("/privacy")}
              />
        } />

        <Route path="/" element={
          token
            ? <HomePage
                apiUrl={API_URL} token={token} user={user}
                onSelectCharacter={handleSelectCharacter}
                onLogout={handleLogout}
                onGoParty={() => navigate("/party")}
                onCreateCharacter={() => navigate("/create")}
                onGoEvents={() => navigate("/events")}
                onGoMyPage={() => navigate("/mypage")}
                onGoRanking={() => navigate("/ranking")}
                onGoNotice={() => navigate("/notice")}
                onGoCommunity={() => navigate("/community")}
              />
            : <HomePage
                apiUrl={API_URL} token="" user={null}
                onSelectCharacter={() => setShowLoginPrompt(true)}
                onLogout={() => navigate("/login")}
                onGoParty={() => setShowLoginPrompt(true)}
                onCreateCharacter={() => setShowLoginPrompt(true)}
                onGoEvents={() => setShowLoginPrompt(true)}
                onGoMyPage={() => setShowLoginPrompt(true)}
                onGoRanking={() => navigate("/ranking")}
                onGoNotice={() => navigate("/notice")}
                onGoCommunity={() => navigate("/community")}
              />
        } />

        <Route path="/chat/:characterId" element={
          token
            ? <ChatRoute apiUrl={API_URL} token={token} user={user} selectedCharacter={selectedCharacter} onSelectCharacter={handleSelectCharacter} onGoCreator={handleGoCreator} />
            : <Navigate to="/" replace />
        } />

        <Route path="/create" element={
          token
            ? <CreateCharacterPage
                apiUrl={API_URL} token={token}
                onBack={() => navigate("/")}
                onCreated={() => navigate("/")}
              />
            : <Navigate to="/" replace />
        } />

        <Route path="/party" element={
          token
            ? <PartyLobbyPage
                apiUrl={API_URL} token={token} user={user}
                onBack={() => navigate("/")}
                onEnterRoom={(code) => navigate(`/party/room/${code}`)}
              />
            : <Navigate to="/" replace />
        } />

        <Route path="/party/room/:roomCode" element={
          token
            ? <PartyRoomRoute apiUrl={API_URL} token={token} user={user} />
            : <Navigate to="/" replace />
        } />

        <Route path="/party/chat/:roomCode" element={
          token
            ? <PartyChatRoute apiUrl={API_URL} token={token} user={user} />
            : <Navigate to="/" replace />
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

// ── URL 파라미터 기반 라우트 래퍼들 ──────────────────────────────

function ChatRoute({ apiUrl, token, user, selectedCharacter, onSelectCharacter, onGoCreator }: {
  apiUrl: string; token: string; user: User | null;
  selectedCharacter: Character | null;
  onSelectCharacter: (c: Character) => void;
  onGoCreator: (id: number) => void;
}) {
  const { characterId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [character, setCharacter] = useState<Character | null>(selectedCharacter);
  const [loading, setLoading] = useState(!selectedCharacter);
  const forceNew = searchParams.get("new") === "1";

  useEffect(() => {
    if (selectedCharacter && selectedCharacter.id === characterId) {
      setCharacter(selectedCharacter);
      setLoading(false);
      return;
    }
    axios.get(`${apiUrl}/characters/${characterId}`)
      .then(res => {
        const c = res.data;
        setCharacter({
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
      .catch(() => navigate("/"))
      .finally(() => setLoading(false));
  }, [characterId]);

  if (loading || !character) return null;

  return (
    <ChatApp
      apiUrl={apiUrl} token={token} user={user}
      character={character}
      forceNewSession={forceNew}
      onBack={() => navigate("/")}
      onSelectCharacter={onSelectCharacter}
      onGoCreator={onGoCreator}
    />
  );
}

function EditCharacterRoute({ apiUrl, token }: { apiUrl: string; token: string | null }) {
  const { id } = useParams();
  const navigate = useNavigate();
  if (!token) return <Navigate to="/" replace />;
  return (
    <EditCharacterPage
      apiUrl={apiUrl} token={token}
      characterId={id ?? ""}
      onBack={() => navigate("/mypage")}
      onSaved={() => navigate("/mypage")}
    />
  );
}

function CreatorRoute({ apiUrl, token, onSelectCharacter }: {
  apiUrl: string; token: string | null; onSelectCharacter: (c: Character) => void;
}) {
  const { userId } = useParams();
  const navigate = useNavigate();
  return (
    <CreatorPage
      apiUrl={apiUrl} token={token ?? ""}
      userId={Number(userId) || 0}
      onBack={() => navigate("/")}
      onSelectCharacter={onSelectCharacter}
    />
  );
}

function PartyRoomRoute({ apiUrl, token, user }: { apiUrl: string; token: string; user: User | null }) {
  const { roomCode } = useParams();
  const navigate = useNavigate();
  return (
    <PartyRoomPage
      apiUrl={apiUrl} token={token} user={user}
      roomCode={roomCode ?? ""}
      onBack={() => navigate("/party")}
      onStartChat={(code) => navigate(`/party/chat/${code}`)}
    />
  );
}

function PartyChatRoute({ apiUrl, token, user }: { apiUrl: string; token: string; user: User | null }) {
  const { roomCode } = useParams();
  const navigate = useNavigate();
  return (
    <PartyChatPage
      apiUrl={apiUrl} token={token} user={user}
      roomCode={roomCode ?? ""}
      onBack={() => navigate(`/party/room/${roomCode}`)}
      onLeave={() => navigate("/")}
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}