import { useState, useEffect } from "react";
import axios from "axios";

interface CharacterImageModalProps {
  apiUrl: string;
  token: string;
  characterId: string;
  characterName: string;
  onClose: () => void;
}

const EMOTIONS = ["neutral", "happy", "sad", "angry", "shy", "surprised", "love", "embarrassed", "crying", "serious"];
const SITUATIONS = ["default", "indoor", "outdoor", "night", "cafe", "forest", "rain", "sunny", "fantasy", "dramatic"];

const EMOTION_LABELS: Record<string, string> = {
  neutral: "기본", happy: "기쁨", sad: "슬픔", angry: "화남",
  shy: "수줍음", surprised: "놀람", love: "사랑", embarrassed: "당황",
  crying: "울음", serious: "진지"
};

const SITUATION_LABELS: Record<string, string> = {
  default: "기본", indoor: "실내", outdoor: "야외", night: "밤",
  cafe: "카페", forest: "숲", rain: "비", sunny: "맑음",
  fantasy: "판타지", dramatic: "드라마틱"
};

export default function CharacterImageModal({ apiUrl, token, characterId, characterName, onClose }: CharacterImageModalProps) {
  const [activeTab, setActiveTab] = useState<"emotion" | "background">("emotion");
  const [emotionImages, setEmotionImages] = useState<Record<string, string>>({});
  const [backgroundImages, setBackgroundImages] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/characters/${characterId}/emotions`, { headers })
      .then(res => setEmotionImages(res.data))
      .catch(console.error);

    axios.get(`${apiUrl}/characters/${characterId}/backgrounds`, { headers })
      .then(res => setBackgroundImages(res.data))
      .catch(console.error);
  }, []);

  const handleEmotionUpload = async (emotion: string, file: File) => {
    setUploading(emotion);
    setMessage("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      await axios.post(`${apiUrl}/characters/${characterId}/emotions/${emotion}`, fd, { headers });

      // 업로드 후 목록 갱신
      const res = await axios.get(`${apiUrl}/characters/${characterId}/emotions`, { headers });
      setEmotionImages(res.data);
      setMessage("업로드 완료!");
    } catch {
      setMessage("업로드 실패");
    } finally {
      setUploading(null);
    }
  };

  const handleBackgroundUpload = async (situation: string, file: File) => {
    setUploading(situation);
    setMessage("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      await axios.post(`${apiUrl}/characters/${characterId}/backgrounds/${situation}`, fd, { headers });

      const res = await axios.get(`${apiUrl}/characters/${characterId}/backgrounds`, { headers });
      setBackgroundImages(res.data);
      setMessage("업로드 완료!");
    } catch {
      setMessage("업로드 실패");
    } finally {
      setUploading(null);
    }
  };

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,.6)",
          backdropFilter: "blur(4px)",
        }}
      />
      <div
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 51,
          width: 500, maxWidth: "92vw",
          maxHeight: "85vh",
          borderRadius: 28,
          border: "1px solid var(--border-default)",
          background: "linear-gradient(180deg, rgba(24,29,54,.98), rgba(9,11,20,.99))",
          boxShadow: "0 0 60px rgba(0,0,0,.5)",
          display: "flex", flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* 헤더 */}
        <div
          style={{
            padding: "20px 24px",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: "1px solid var(--border-subtle)",
            flexShrink: 0,
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 16 }}>{characterName} 이미지 관리</div>
          <button
            onClick={onClose}
            style={{
              width: 32, height: 32, borderRadius: 8,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-muted)", cursor: "pointer", fontSize: 16,
            }}
          >
            ×
          </button>
        </div>

        {/* 탭 */}
        <div style={{ display: "flex", borderBottom: "1px solid var(--border-subtle)", flexShrink: 0 }}>
          {[
            { id: "emotion", label: "감정 이미지" },
            { id: "background", label: "배경 이미지" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                flex: 1, padding: "14px", border: "none",
                background: activeTab === tab.id ? "rgba(139,124,255,.12)" : "transparent",
                color: activeTab === tab.id ? "var(--primary)" : "var(--text-muted)",
                fontWeight: 600, fontSize: 14, cursor: "pointer",
                borderBottom: activeTab === tab.id ? "2px solid var(--primary)" : "2px solid transparent",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {message && (
          <div style={{
            padding: "8px 24px",
            color: message.includes("실패") ? "#ff6b8a" : "#49d89a",
            fontSize: 13, flexShrink: 0,
          }}>
            {message}
          </div>
        )}

        {/* 내용 */}
        <div style={{ overflowY: "auto", flex: 1, padding: 20 }}>
          {activeTab === "emotion" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {EMOTIONS.map(emotion => (
                <div
                  key={emotion}
                  style={{
                    borderRadius: 16, border: "1px solid var(--border-default)",
                    background: "rgba(255,255,255,.02)", padding: 14,
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 10,
                  }}
                >
                  {emotionImages[emotion] ? (
                    <img
                      src={emotionImages[emotion]}
                      alt={emotion}
                      style={{ width: 80, height: 80, borderRadius: 12, objectFit: "cover" }}
                    />
                  ) : (
                    <div
                      style={{
                        width: 80, height: 80, borderRadius: 12,
                        background: "rgba(139,124,255,.1)",
                        display: "grid", placeItems: "center", fontSize: 28,
                      }}
                    >
                      +
                    </div>
                  )}
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{EMOTION_LABELS[emotion]}</div>
                  <input
                    type="file" accept="image/*"
                    id={`emotion-${emotion}`}
                    style={{ display: "none" }}
                    onChange={e => {
                      const f = e.target.files?.[0];
                      if (f) handleEmotionUpload(emotion, f);
                    }}
                  />
                  <label
                    htmlFor={`emotion-${emotion}`}
                    style={{
                      padding: "6px 14px", borderRadius: 10,
                      border: "1px solid var(--primary)",
                      background: "rgba(139,124,255,.1)",
                      color: "var(--primary)", fontSize: 12,
                      fontWeight: 600, cursor: "pointer",
                      opacity: uploading === emotion ? 0.6 : 1,
                    }}
                  >
                    {uploading === emotion ? "업로드 중..." : emotionImages[emotion] ? "변경" : "업로드"}
                  </label>
                </div>
              ))}
            </div>
          )}

          {activeTab === "background" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {SITUATIONS.map(situation => (
                <div
                  key={situation}
                  style={{
                    borderRadius: 16, border: "1px solid var(--border-default)",
                    background: "rgba(255,255,255,.02)", padding: 14,
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 10,
                  }}
                >
                  {backgroundImages[situation] ? (
                    <img
                      src={backgroundImages[situation]}
                      alt={situation}
                      style={{ width: "100%", height: 70, borderRadius: 12, objectFit: "cover" }}
                    />
                  ) : (
                    <div
                      style={{
                        width: "100%", height: 70, borderRadius: 12,
                        background: "rgba(95,214,255,.08)",
                        display: "grid", placeItems: "center", fontSize: 28,
                      }}
                    >
                      🌌
                    </div>
                  )}
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{SITUATION_LABELS[situation]}</div>
                  <input
                    type="file" accept="image/*"
                    id={`bg-${situation}`}
                    style={{ display: "none" }}
                    onChange={e => {
                      const f = e.target.files?.[0];
                      if (f) handleBackgroundUpload(situation, f);
                    }}
                  />
                  <label
                    htmlFor={`bg-${situation}`}
                    style={{
                      padding: "6px 14px", borderRadius: 10,
                      border: "1px solid var(--secondary)",
                      background: "rgba(95,214,255,.08)",
                      color: "var(--secondary)", fontSize: 12,
                      fontWeight: 600, cursor: "pointer",
                      opacity: uploading === situation ? 0.6 : 1,
                    }}
                  >
                    {uploading === situation ? "업로드 중..." : backgroundImages[situation] ? "변경" : "업로드"}
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}