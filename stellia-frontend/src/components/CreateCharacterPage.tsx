import { useState } from "react";
import axios from "axios";

interface CreateCharacterPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
  onCreated: () => void;
}

export default function CreateCharacterPage({ apiUrl, token, onBack, onCreated }: CreateCharacterPageProps) {
  const [activeTab, setActiveTab] = useState<"profile" | "detail" | "situation" | "setting">("profile");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    age: 20,
    job: "",
    personality: "",
    likes: "",
    dislikes: "",
    speech_style: "",
    situation: "",
    first_message: "",
    visibility: "public",
    is_adult: 0,
    image_url: "",
    tags: [] as string[],
  });

  const [tagInput, setTagInput] = useState("");

  const update = (key: string, value: unknown) =>
    setFormData(prev => ({ ...prev, [key]: value }));

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      update("tags", [...formData.tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const removeTag = (tag: string) =>
    update("tags", formData.tags.filter(t => t !== tag));

  const handleSubmit = async () => {
    if (!formData.name || !formData.personality || !formData.speech_style) {
      setError("이름, 성격, 말투는 필수예요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await axios.post(`${apiUrl}/characters`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      onCreated();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "캐릭터 생성에 실패했어요.");
      }
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: "profile", label: "프로필" },
    { id: "detail", label: "상세정보" },
    { id: "situation", label: "시작상황" },
    { id: "setting", label: "기타설정" },
  ] as const;

  const inputStyle = {
    padding: "14px 18px",
    borderRadius: 14,
    border: "1px solid var(--border-default)",
    background: "rgba(255,255,255,.04)",
    color: "var(--text-primary)",
    fontSize: 15,
    outline: "none",
    width: "100%",
    boxSizing: "border-box" as const,
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: 100,
    resize: "vertical" as const,
  };

  return (
    <div
      style={{
        position: "relative",
        zIndex: 2,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        maxWidth: 600,
        margin: "0 auto",
        padding: "24px",
        overflowY: "auto",
      }}
    >
      {/* 헤더 */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28 }}>
        <button
          onClick={onBack}
          style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-primary)",
            fontSize: 18,
          }}
        >
          ←
        </button>
        <div
          style={{
            fontSize: 22,
            fontWeight: 700,
            background: "var(--gradient-cosmic)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          캐릭터 만들기
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
          marginBottom: 24,
        }}
      >
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1,
              padding: "12px",
              border: "none",
              background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600,
              fontSize: 13,
              transition: "all .2s ease",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 폼 */}
      <div className="glass-card" style={{ borderRadius: 24, padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>

        {activeTab === "profile" && (
          <>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>이름 *</label>
              <input style={inputStyle} placeholder="캐릭터 이름" value={formData.name} onChange={e => update("name", e.target.value)} />
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>소개</label>
              <textarea style={textareaStyle} placeholder="캐릭터 소개를 입력해주세요" value={formData.description} onChange={e => update("description", e.target.value)} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>나이</label>
                <input style={inputStyle} type="number" value={formData.age} onChange={e => update("age", parseInt(e.target.value) || 20)} />
              </div>
              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>직업</label>
                <input style={inputStyle} placeholder="예: 대학생" value={formData.job} onChange={e => update("job", e.target.value)} />
              </div>
            </div>
            <button
              onClick={() => setActiveTab("detail")}
              style={{
                padding: "14px",
                borderRadius: 14,
                border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff",
                fontWeight: 700,
                fontSize: 15,
              }}
            >
              다음 →
            </button>
          </>
        )}

        {activeTab === "detail" && (
          <>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>성격 *</label>
              <textarea style={textareaStyle} placeholder="성격을 상세히 입력해주세요" value={formData.personality} onChange={e => update("personality", e.target.value)} />
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>좋아하는 것</label>
              <input style={inputStyle} placeholder="예: 커피, 독서" value={formData.likes} onChange={e => update("likes", e.target.value)} />
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>싫어하는 것</label>
              <input style={inputStyle} placeholder="예: 거짓말" value={formData.dislikes} onChange={e => update("dislikes", e.target.value)} />
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>말투 *</label>
              <textarea style={textareaStyle} placeholder="말투를 입력해주세요. 예: 부드럽고 따뜻한 말투" value={formData.speech_style} onChange={e => update("speech_style", e.target.value)} />
            </div>
            <button
              onClick={() => setActiveTab("situation")}
              style={{
                padding: "14px",
                borderRadius: 14,
                border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff",
                fontWeight: 700,
                fontSize: 15,
              }}
            >
              다음 →
            </button>
          </>
        )}

        {activeTab === "situation" && (
          <>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>시작 상황</label>
              <textarea style={textareaStyle} placeholder="첫 만남 상황을 설정해주세요" value={formData.situation} onChange={e => update("situation", e.target.value)} />
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>첫 대사</label>
              <textarea style={textareaStyle} placeholder="캐릭터가 처음 건네는 말" value={formData.first_message} onChange={e => update("first_message", e.target.value)} />
            </div>
            <button
              onClick={() => setActiveTab("setting")}
              style={{
                padding: "14px",
                borderRadius: 14,
                border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff",
                fontWeight: 700,
                fontSize: 15,
              }}
            >
              다음 →
            </button>
          </>
        )}

        {activeTab === "setting" && (
          <>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>태그</label>
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                <input
                  style={{ ...inputStyle, flex: 1 }}
                  placeholder="태그 입력 후 추가"
                  value={tagInput}
                  onChange={e => setTagInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && addTag()}
                />
                <button
                  onClick={addTag}
                  style={{
                    padding: "14px 18px",
                    borderRadius: 14,
                    border: "1px solid var(--primary)",
                    background: "rgba(139,124,255,.12)",
                    color: "var(--primary)",
                    fontWeight: 600,
                  }}
                >
                  추가
                </button>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {formData.tags.map(tag => (
                  <span
                    key={tag}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 999,
                      background: "rgba(139,124,255,.12)",
                      border: "1px solid rgba(139,124,255,.3)",
                      color: "var(--primary)",
                      fontSize: 13,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", padding: 0 }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>공개 설정</label>
              <div style={{ display: "flex", gap: 10 }}>
                {["public", "private"].map(v => (
                  <button
                    key={v}
                    onClick={() => update("visibility", v)}
                    style={{
                      flex: 1,
                      padding: "12px",
                      borderRadius: 14,
                      border: formData.visibility === v ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.visibility === v ? "rgba(139,124,255,.15)" : "rgba(255,255,255,.02)",
                      color: formData.visibility === v ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600,
                    }}
                  >
                    {v === "public" ? "공개" : "비공개"}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div style={{ color: "#ff6b8a", fontSize: 13, textAlign: "center" }}>{error}</div>
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
                opacity: loading ? 0.7 : 1,
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 0 30px rgba(139,124,255,.3)",
              }}
            >
              {loading ? "생성 중..." : "캐릭터 생성 완료"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}