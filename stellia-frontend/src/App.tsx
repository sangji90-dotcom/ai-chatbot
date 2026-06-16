import { useState } from "react";
import StarBackground from "./components/StarBackground";
import LoginPage from "./components/LoginPage";
import HomePage from "./components/HomePage";
import ChatApp from "./components/ChatApp";

export interface Character {
  id: string;
  name: string;
  title: string;
  avatar: string;
  description: string;
  online: boolean;
  tags: string[];
  user_id?: number;
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
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("access_token")
  );
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<"home" | "chat">("home");
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);

  const handleLogin = (accessToken: string, userData: User) => {
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setUser(null);
    setView("home");
    setSelectedCharacter(null);
  };

  const handleSelectCharacter = (char: Character) => {
    setSelectedCharacter(char);
    setView("chat");
  };

  return (
    <>
      <StarBackground />
      {!token ? (
        <LoginPage apiUrl={API_URL} onLogin={handleLogin} />
      ) : view === "home" ? (
        <HomePage
          apiUrl={API_URL}
          token={token}
          user={user}
          onSelectCharacter={handleSelectCharacter}
          onLogout={handleLogout}
        />
      ) : (
        <ChatApp
          apiUrl={API_URL}
          token={token}
          user={user}
          character={selectedCharacter!}
          onBack={() => setView("home")}
          onSelectCharacter={handleSelectCharacter}
        />
      )}
    </>
  );
}