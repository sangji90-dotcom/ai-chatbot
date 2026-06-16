import { useState } from "react";
import axios from "axios";
import type { User } from "../App";

interface LoginPageProps {
  apiUrl: string;
  onLogin: (token: string, user: User) => void;
}

export default function LoginPage({ apiUrl, onLogin }: LoginPageProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        const res = await axios.post(`${apiUrl}/auth/register`, {
          email,
          username,
          password,
        });
        localStorage.setItem("refresh_token", res.data.refresh_token);
        const userRes = await axios.get(`${apiUrl}/users/me`, {
          headers: { Authorization: `Bearer ${res.data.access_token}` },
        });
        onLogin(res.data.access_token, userRes.data);
      } else {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        const res = await axios.post(`${apiUrl}/auth/login`, formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
        localStorage.setItem("refresh_token", res.data.refresh_token);
        const userRes = await axios.get(`${apiUrl}/users/me`, {
          headers: { Authorization: `Bearer ${res.data.access_token}` },
        });
        onLogin(res.data.access_token, userRes.data);
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "오류가 발생했습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "relative",
        zIndex: 10,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
      }}
    >
      <div
        className="glass-card"
        style={{
          width: 400,
          borderRadius: 28,
          padding: 40,
          display: "flex",
          flexDirection: "column",
          gap: 24,
        }}
      >
        {/* 로고 */}
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize: 42,
              fontWeight: 800,
              background: "var(--gradient-cosmic)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Stellia
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 6 }}>
            Meet Fate. Beyond Worlds.
          </div>
        </div>

        {/* 탭 */}
        <div
          style={{
            display: "flex",
            borderRadius: 16,
            background: "rgba(255,255,255,.04)",
            border: "1px solid var(--border-default)",
            overflow: "hidden",
          }}
        >
          {["로그인", "회원가입"].map((tab, i) => (
            <button
              key={tab}
              onClick={() => { setIsRegister(i === 1); setError(""); }}
              style={{
                flex: 1,
                padding: "12px",
                border: "none",
                background: isRegister === (i === 1)
                  ? "var(--gradient-cosmic)"
                  : "transparent",
                color: isRegister === (i === 1) ? "#fff" : "var(--text-muted)",
                fontWeight: 600,
                fontSize: 14,
                transition: "all .2s ease",
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* 입력 폼 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {isRegister && (
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="닉네임"
              style={{
                padding: "14px 18px",
                borderRadius: 14,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.04)",
                color: "var(--text-primary)",
                fontSize: 15,
                outline: "none",
              }}
            />
          )}
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일"
            type="email"
            style={{
              padding: "14px 18px",
              borderRadius: 14,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-primary)",
              fontSize: 15,
              outline: "none",
            }}
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호"
            type="password"
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            style={{
              padding: "14px 18px",
              borderRadius: 14,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-primary)",
              fontSize: 15,
              outline: "none",
            }}
          />
        </div>

        {error && (
          <div style={{ color: "#ff6b8a", fontSize: 13, textAlign: "center" }}>
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            padding: "16px",
            borderRadius: 16,
            border: "none",
            background: "var(--gradient-cosmic)",
            color: "#fff",
            fontWeight: 700,
            fontSize: 16,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
            boxShadow: "0 0 30px rgba(139,124,255,.3)",
            transition: "all .2s ease",
          }}
        >
          {loading ? "처리 중..." : isRegister ? "회원가입" : "로그인"}
        </button>
      </div>
    </div>
  );
}