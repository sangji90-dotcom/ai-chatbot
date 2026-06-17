import { useState } from "react";
import axios from "axios";

interface CreateCharacterPageProps {
  apiUrl: string;
  token: string;
  onBack: () => void;
  onCreated: () => void;
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

const CATEGORIES = ["시뮬레이션", "로맨스", "판타지/SF", "드라마", "무협/사극", "GL", "BL", "공포/추리", "액션", "코믹/일상", "스포츠/학원", "기타"];

export default function CreateCharacterPage({ apiUrl, token, onBack, onCreated }: CreateCharacterPageProps) {
  const [activeTab, setActiveTab] = useState<"profile" | "detail" | "images" | "situation" | "setting">("profile");
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
    category: "",
  });

  // 이미지 파일 임시 저장
  const [emotionFiles, setEmotionFiles] = useState<Record<string, File>>({});
  const [emotionPreviews, setEmotionPreviews] = useState<Record<string, string>>({});
  const [backgroundFiles, setBackgroundFiles] = useState<Record<string, File>>({});
  const [backgroundPreviews, setBackgroundPreviews] = useState<Record<string, string>>({});
  const [mainImageFile, setMainImageFile] = useState<File | null>(null);

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

  const handleEmotionImage = (emotion: string, file: File) => {
    setEmotionFiles(prev => ({ ...prev, [emotion]: file }));
    const reader = new FileReader();
    reader.onload = () => setEmotionPreviews(prev => ({ ...prev, [emotion]: reader.result as string }));
    reader.readAsDataURL(file);
  };

  const handleBackgroundImage = (situation: string, file: File) => {
    setBackgroundFiles(prev => ({ ...prev, [situation]: file }));
    const reader = new FileReader();
    reader.onload = () => setBackgroundPreviews(prev => ({ ...prev, [situation]: reader.result as string }));
    reader.readAsDataURL(file);
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.personality || !formData.speech_style) {
      setError("이름, 성격, 말투는 필수예요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const headers = { Authorization: `Bearer ${token}` };

      // 1. 캐릭터 생성
      const submitData = {
        ...formData,
        image_url: formData.image_url.startsWith("data:") ? "" : formData.image_url,
      };
      const res = await axios.post(`${apiUrl}/characters`, submitData, { headers });
      const characterId = res.data.id;

      // 2. 메인 이미지 업로드
      if (mainImageFile) {
        const fd = new FormData();
        fd.append("file", mainImageFile);
        await axios.post(`${apiUrl}/characters/${characterId}/image`, fd, { headers });
      }

      // 3. 감정 이미지 업로드
      for (const [emotion, file] of Object.entries(emotionFiles)) {
        const fd = new FormData();
        fd.append("file", file);
        await axios.post(`${apiUrl}/characters/${characterId}/emotions/${emotion}`, fd, { headers });
      }

      // 4. 배경 이미지 업로드
      for (const [situation, file] of Object.entries(backgroundFiles)) {
        const fd = new FormData();
        fd.append("file", file);
        await axios.post(`${apiUrl}/characters/${characterId}/backgrounds/${situation}`, fd, { headers });
      }

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
    { id: "images", label: "이미지" },
    { id: "situation", label: "시작상황" },
    { id: "setting", label: "기타설정" },
  ] as const;

  const inputStyle = {
    padding: "14px 18px", borderRadius: 14,
    border: "1px solid var(--border-default)",
    background: "rgba(255,255,255,.04)",
    color: "var(--text-primary)", fontSize: 15,
    outline: "none", width: "100%",
    boxSizing: "border-box" as const,
  };

  const textareaStyle = {
    ...inputStyle, minHeight: 100,
    resize: "vertical" as const,
  };

  return (
    <div
      style={{
        position: "relative", zIndex: 2,
        height: "100vh", display: "flex", flexDirection: "column",
        maxWidth: 600, margin: "0 auto",
        padding: "24px", overflowY: "auto",
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
            color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
          }}
        >
          ←
        </button>
        <div
          style={{
            fontSize: 22, fontWeight: 700,
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
          display: "flex", borderRadius: 16,
          background: "rgba(255,255,255,.04)",
          border: "1px solid var(--border-default)",
          overflow: "hidden", marginBottom: 24,
        }}
      >
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1, padding: "12px", border: "none",
              background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 11, transition: "all .2s ease", cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 폼 */}
      <div className="glass-card" style={{ borderRadius: 24, padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>

        {/* 프로필 탭 */}
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
            <button onClick={() => setActiveTab("detail")} style={{ padding: "14px", borderRadius: 14, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
              다음 →
            </button>
          </>
        )}

        {/* 상세정보 탭 */}
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
              <textarea style={textareaStyle} placeholder="말투를 입력해주세요" value={formData.speech_style} onChange={e => update("speech_style", e.target.value)} />
            </div>
            <button onClick={() => setActiveTab("images")} style={{ padding: "14px", borderRadius: 14, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
              다음 →
            </button>
          </>
        )}

        {/* 이미지 탭 */}
        {activeTab === "images" && (
          <>
            {/* 메인 이미지 */}
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>메인 이미지</label>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: 20, borderRadius: 16, border: "1px dashed var(--border-default)", background: "rgba(255,255,255,.02)" }}>
                {mainImageFile ? (
                  <img src={URL.createObjectURL(mainImageFile)} alt="메인" style={{ width: 120, height: 120, borderRadius: "50%", objectFit: "cover" }} />
                ) : (
                  <div style={{ width: 120, height: 120, borderRadius: "50%", background: "var(--gradient-cosmic)", display: "grid", placeItems: "center", fontSize: 40, fontWeight: 700 }}>
                    {formData.name?.[0] || "?"}
                  </div>
                )}
                <input type="file" accept="image/*" id="main-image" style={{ display: "none" }}
                  onChange={e => { const f = e.target.files?.[0]; if (f) setMainImageFile(f); }} />
                <label htmlFor="main-image" style={{ padding: "10px 20px", borderRadius: 12, border: "1px solid var(--primary)", background: "rgba(139,124,255,.12)", color: "var(--primary)", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                  이미지 선택
                </label>
              </div>
            </div>

            {/* 감정별 이미지 */}
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>감정별 이미지</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {EMOTIONS.map(emotion => (
                  <div key={emotion} style={{ borderRadius: 14, border: "1px solid var(--border-default)", background: "rgba(255,255,255,.02)", padding: 12, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                    {emotionPreviews[emotion] ? (
                      <img src={emotionPreviews[emotion]} alt={emotion} style={{ width: 60, height: 60, borderRadius: 10, objectFit: "cover" }} />
                    ) : (
                      <div style={{ width: 60, height: 60, borderRadius: 10, background: "rgba(139,124,255,.12)", display: "grid", placeItems: "center", fontSize: 24 }}>+</div>
                    )}
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{EMOTION_LABELS[emotion]}</div>
                    <input type="file" accept="image/*" id={`emotion-${emotion}`} style={{ display: "none" }}
                      onChange={e => { const f = e.target.files?.[0]; if (f) handleEmotionImage(emotion, f); }} />
                    <label htmlFor={`emotion-${emotion}`} style={{ fontSize: 11, color: "var(--primary)", cursor: "pointer" }}>
                      {emotionFiles[emotion] ? "변경" : "업로드"}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* 배경별 이미지 */}
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>상황별 배경</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {SITUATIONS.map(situation => (
                  <div key={situation} style={{ borderRadius: 14, border: "1px solid var(--border-default)", background: "rgba(255,255,255,.02)", padding: 12, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                    {backgroundPreviews[situation] ? (
                      <img src={backgroundPreviews[situation]} alt={situation} style={{ width: "100%", height: 60, borderRadius: 10, objectFit: "cover" }} />
                    ) : (
                      <div style={{ width: "100%", height: 60, borderRadius: 10, background: "rgba(95,214,255,.08)", display: "grid", placeItems: "center", fontSize: 24 }}>🌌</div>
                    )}
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{SITUATION_LABELS[situation]}</div>
                    <input type="file" accept="image/*" id={`bg-${situation}`} style={{ display: "none" }}
                      onChange={e => { const f = e.target.files?.[0]; if (f) handleBackgroundImage(situation, f); }} />
                    <label htmlFor={`bg-${situation}`} style={{ fontSize: 11, color: "var(--secondary)", cursor: "pointer" }}>
                      {backgroundFiles[situation] ? "변경" : "업로드"}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <button onClick={() => setActiveTab("situation")} style={{ padding: "14px", borderRadius: 14, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
              다음 →
            </button>
          </>
        )}

        {/* 시작상황 탭 */}
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
            <button onClick={() => setActiveTab("setting")} style={{ padding: "14px", borderRadius: 14, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
              다음 →
            </button>
          </>
        )}

        {/* 기타설정 탭 */}
        {activeTab === "setting" && (
          <>
            {/* 공개 범위 */}
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>공개 범위</label>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[
                  { value: "public", label: "모든 사용자가 이용 가능해요", icon: "🟢" },
                  { value: "private", label: "나만 이용 가능해요", icon: "🔒" },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => update("visibility", opt.value)}
                    style={{
                      padding: "14px 16px", borderRadius: 14, textAlign: "left",
                      border: formData.visibility === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.visibility === opt.value ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.visibility === opt.value ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 10,
                    }}
                  >
                    <span>{opt.icon}</span>{opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 성인 설정 */}
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>이용 제한</label>
              <div style={{ display: "flex", gap: 10 }}>
                {[{ label: "전체 이용가", value: 0 }, { label: "성인 전용", value: 1 }].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => update("is_adult", opt.value)}
                    style={{
                      flex: 1, padding: "12px", borderRadius: 14,
                      border: formData.is_adult === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.is_adult === opt.value ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.is_adult === opt.value ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 카테고리 */}
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>카테고리</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                {CATEGORIES.map(cat => (
                  <button
                    key={cat}
                    onClick={() => update("category", cat)}
                    style={{
                      padding: "10px 8px", borderRadius: 12, fontSize: 13,
                      border: formData.category === cat ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.category === cat ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.category === cat ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer",
                    }}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* 태그 */}
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
                <button onClick={addTag} style={{ padding: "14px 18px", borderRadius: 14, border: "1px solid var(--primary)", background: "rgba(139,124,255,.12)", color: "var(--primary)", fontWeight: 600, cursor: "pointer" }}>
                  추가
                </button>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {formData.tags.map(tag => (
                  <span key={tag} style={{ padding: "6px 12px", borderRadius: 999, background: "rgba(139,124,255,.12)", border: "1px solid rgba(139,124,255,.3)", color: "var(--primary)", fontSize: 13, display: "flex", alignItems: "center", gap: 6 }}>
                    {tag}
                    <button onClick={() => removeTag(tag)} style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", padding: 0 }}>×</button>
                  </span>
                ))}
              </div>
            </div>

            {error && <div style={{ color: "#ff6b8a", fontSize: 13, textAlign: "center" }}>{error}</div>}

            {loading && (
              <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: 14 }}>
                캐릭터 생성 중... 이미지 업로드 중...
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              style={{
                padding: "16px", borderRadius: 16, border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 700, fontSize: 16,
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