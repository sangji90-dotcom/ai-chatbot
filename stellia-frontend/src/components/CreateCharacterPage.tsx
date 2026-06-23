import { useState } from "react";
import axios from "axios";
import PolicyModal from "./PolicyModal";
import { useToast } from "./Toast";

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

const TEMPLATES = {
  "일반 대화": {
    personality: "따뜻하고 친근한 성격. 상대방의 말을 잘 들어주고 공감을 잘 함. 유머 감각이 있으며 대화를 즐김.",
    speech_style: "편안하고 자연스러운 말투. 존댓말과 반말을 상황에 따라 사용. 이모티콘을 적당히 사용.",
    first_message: "안녕! 오늘 어떤 하루였어? 나한테 뭐든 얘기해도 돼 😊",
  },
  "시뮬레이션": {
    personality: "공정하고 일관된 게임 진행자. 규칙을 정확히 지키며 결과를 명확하게 알려줌. 유저의 선택을 존중함.",
    speech_style: "명확하고 간결한 진행 말투. 게임 결과는 항상 같은 형식으로 출력. 규칙 위반 시 친절하게 안내.",
    first_message: "게임을 시작합니다! 기본 포인트 50P가 지급됐어요. 명령어를 입력해주세요.\n\n📋 명령어 목록\n• 뽑기 - 가챠 진행 (10P)\n• 인벤토리 - 보유 아이템 확인\n• 포인트 - 현재 포인트 확인",
  },
  "롤플레이": {
    personality: "몰입감 있는 캐릭터 연기. 세계관에 충실하며 상황에 맞게 반응함. AI라는 사실을 절대 드러내지 않음.",
    speech_style: "캐릭터에 맞는 말투와 어투. 세계관의 언어와 표현 방식을 사용. 감정 표현이 풍부하고 생동감 있음.",
    first_message: "...당신이군요. 이곳까지 오다니 대단합니다. 무슨 용건으로 왔습니까?",
  },
  "학원물": {
    personality: "활발하고 밝은 학생 캐릭터. 학교생활에 열정적이며 친구들과 잘 어울림. 약간의 고민도 있는 현실적인 모습.",
    speech_style: "또래 친구에게 말하듯 자연스럽고 가벼운 말투. 학교 용어와 유행어를 자연스럽게 사용. 감탄사 적절히 활용.",
    first_message: "야, 오늘 체육 시간에 진짜 죽는 줄 알았다ㅋㅋ 너는 어땠어?",
  },
  "판타지": {
    personality: "신비롭고 강인한 판타지 세계의 존재. 특별한 능력과 과거를 지님. 인간 세계에 대한 호기심과 경계심이 공존.",
    speech_style: "고풍스럽고 품위 있는 말투. 판타지 세계의 표현과 단어를 사용. 감정을 절제하되 깊이 있게 표현.",
    first_message: "오랜만에 인간을 만나는군요. 이 어두운 숲에서 무엇을 찾고 있습니까?",
  },
};

export default function CreateCharacterPage({ apiUrl, token, onBack, onCreated }: CreateCharacterPageProps) {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<"profile" | "detail" | "images" | "situation" | "setting">("profile");
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [showPolicy, setShowPolicy] = useState(true);

  const [formData, setFormData] = useState({
    name: "", description: "", age: 20, job: "",
    personality: "", likes: "", dislikes: "", speech_style: "",
    situation: "", first_message: "",
    visibility: "public", is_adult: 0, image_url: "",
    tags: [] as string[], category: "", party_enabled: 0,
  });

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

  const handleAutoComplete = async () => {
    if (!formData.name) return;
    setAiLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const res = await axios.post(`${apiUrl}/characters/auto-complete`, {
        name: formData.name, description: formData.description,
        job: formData.job, age: formData.age,
      }, { headers });
      if (res.data.personality) update("personality", res.data.personality);
      if (res.data.speech_style) update("speech_style", res.data.speech_style);
      if (res.data.likes) update("likes", res.data.likes);
      if (res.data.dislikes) update("dislikes", res.data.dislikes);
      if (res.data.first_message) update("first_message", res.data.first_message);
      if (res.data.situation) update("situation", res.data.situation);
      toast.success("AI 자동완성 완료!");
    } catch {
      toast.error("AI 자동완성에 실패했어요.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.personality || !formData.speech_style) {
      toast.error("이름, 성격, 말투는 필수예요.");
      return;
    }
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const submitData = { ...formData, image_url: "" };
      const res = await axios.post(`${apiUrl}/characters`, submitData, { headers });
      const characterId = res.data.id;

      if (mainImageFile) {
        const fd = new FormData();
        fd.append("file", mainImageFile as File);
        await axios.post(`${apiUrl}/characters/${characterId}/image`, fd, { headers });
      }

      for (const [emotion, file] of Object.entries(emotionFiles)) {
        const fd = new FormData();
        fd.append("file", file);
        await axios.post(`${apiUrl}/characters/${characterId}/emotions/${emotion}`, fd, { headers });
      }

      for (const [situation, file] of Object.entries(backgroundFiles)) {
        const fd = new FormData();
        fd.append("file", file);
        await axios.post(`${apiUrl}/characters/${characterId}/backgrounds/${situation}`, fd, { headers });
      }

      toast.success("캐릭터 생성 완료!");
      onCreated();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.detail || "캐릭터 생성에 실패했어요.");
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
    <>
      {showPolicy && (
        <PolicyModal onAgree={() => setShowPolicy(false)} onClose={onBack} />
      )}
      <div style={{
        position: "relative", zIndex: 2,
        height: "100vh", display: "flex", flexDirection: "column",
        maxWidth: 600, margin: "0 auto",
        padding: "24px", overflowY: "auto",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28 }}>
          <button onClick={onBack} style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-primary)", fontSize: 18, cursor: "pointer",
          }}>←</button>
          <div style={{
            fontSize: 22, fontWeight: 700,
            background: "var(--gradient-cosmic)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}>캐릭터 만들기</div>
        </div>

        <div style={{
          display: "flex", borderRadius: 16,
          background: "rgba(255,255,255,.04)",
          border: "1px solid var(--border-default)",
          overflow: "hidden", marginBottom: 24,
        }}>
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              flex: 1, padding: "12px", border: "none",
              background: activeTab === tab.id ? "var(--gradient-cosmic)" : "transparent",
              color: activeTab === tab.id ? "#fff" : "var(--text-muted)",
              fontWeight: 600, fontSize: 11, transition: "all .2s ease", cursor: "pointer",
            }}>{tab.label}</button>
          ))}
        </div>

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
              <button onClick={() => setActiveTab("detail")} style={{ padding: "14px", borderRadius: 14, border: "none", background: "var(--gradient-cosmic)", color: "#fff", fontWeight: 700, fontSize: 15, cursor: "pointer" }}>
                다음 →
              </button>
            </>
          )}

          {activeTab === "detail" && (
            <>
              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 10, display: "block" }}>템플릿으로 빠르게 시작하기</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {Object.keys(TEMPLATES).map(key => (
                    <button key={key} onClick={() => {
                      const t = TEMPLATES[key as keyof typeof TEMPLATES];
                      update("personality", t.personality);
                      update("speech_style", t.speech_style);
                      update("first_message", t.first_message);
                    }} style={{
                      padding: "8px 16px", borderRadius: 999, fontSize: 13,
                      border: "1px solid var(--border-default)",
                      background: "rgba(255,255,255,.04)",
                      color: "var(--text-secondary)", cursor: "pointer",
                    }}>{key}</button>
                  ))}
                </div>
              </div>

              <div>
                <button onClick={handleAutoComplete} disabled={!formData.name || aiLoading} style={{
                  width: "100%", padding: "12px", borderRadius: 14,
                  border: "1px solid rgba(246,198,91,.4)",
                  background: "linear-gradient(135deg, rgba(246,198,91,.15), rgba(246,198,91,.05))",
                  color: "var(--gold)", fontWeight: 600, fontSize: 14,
                  cursor: !formData.name || aiLoading ? "not-allowed" : "pointer",
                  opacity: !formData.name ? 0.5 : 1,
                }}>
                  {aiLoading ? "AI 생성 중..." : "✦ AI 자동완성 (이름/소개 기반)"}
                </button>
                {!formData.name && (
                  <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 6, textAlign: "center" }}>
                    프로필 탭에서 이름을 먼저 입력해주세요
                  </div>
                )}
              </div>

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

          {activeTab === "images" && (
            <>
              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>메인 이미지</label>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: 20, borderRadius: 16, border: "1px dashed var(--border-default)", background: "rgba(255,255,255,.02)" }}>
                  {mainImageFile ? (
                    <img src={URL.createObjectURL(mainImageFile as Blob)} alt="메인" style={{ width: 120, height: 120, borderRadius: "50%", objectFit: "cover" }} />
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

          {activeTab === "setting" && (
            <>
              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>공개 범위</label>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {[
                    { value: "public", label: "모든 사용자가 이용 가능해요", icon: "🟢" },
                    { value: "private", label: "나만 이용 가능해요", icon: "🔒" },
                  ].map(opt => (
                    <button key={opt.value} onClick={() => update("visibility", opt.value)} style={{
                      padding: "14px 16px", borderRadius: 14, textAlign: "left",
                      border: formData.visibility === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.visibility === opt.value ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.visibility === opt.value ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 10,
                    }}>
                      <span>{opt.icon}</span>{opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>이용 제한</label>
                <div style={{ display: "flex", gap: 10 }}>
                  {[{ label: "전체 이용가", value: 0 }, { label: "성인 전용", value: 1 }].map(opt => (
                    <button key={opt.value} onClick={() => update("is_adult", opt.value)} style={{
                      flex: 1, padding: "12px", borderRadius: 14,
                      border: formData.is_adult === opt.value ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.is_adult === opt.value ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.is_adult === opt.value ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer",
                    }}>{opt.label}</button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>카테고리</label>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                  {CATEGORIES.map(cat => (
                    <button key={cat} onClick={() => update("category", cat)} style={{
                      padding: "10px 8px", borderRadius: 12, fontSize: 13,
                      border: formData.category === cat ? "1px solid var(--primary)" : "1px solid var(--border-default)",
                      background: formData.category === cat ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.category === cat ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer",
                    }}>{cat}</button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 12, display: "block" }}>파티챗</label>
                <div style={{ display: "flex", gap: 10 }}>
                  {[{ label: "비활성화", value: 0 }, { label: "활성화", value: 1 }].map(opt => (
                    <button key={opt.value} onClick={() => update("party_enabled", opt.value)} style={{
                      flex: 1, padding: "12px", borderRadius: 14,
                      border: formData.party_enabled === opt.value ? "1px solid rgba(139,124,255,.6)" : "1px solid var(--border-default)",
                      background: formData.party_enabled === opt.value ? "rgba(139,124,255,.12)" : "rgba(255,255,255,.02)",
                      color: formData.party_enabled === opt.value ? "var(--primary)" : "var(--text-muted)",
                      fontWeight: 600, cursor: "pointer",
                    }}>{opt.label}</button>
                  ))}
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>
                  활성화 시 캐릭터 프로필에서 파티챗 방 만들기 버튼이 표시돼요.
                </div>
              </div>

              <div>
                <label style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8, display: "block" }}>태그</label>
                <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                  <input style={{ ...inputStyle, flex: 1 }} placeholder="태그 입력 후 추가"
                    value={tagInput} onChange={e => setTagInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && addTag()} />
                  <button onClick={addTag} style={{ padding: "14px 18px", borderRadius: 14, border: "1px solid var(--primary)", background: "rgba(139,124,255,.12)", color: "var(--primary)", fontWeight: 600, cursor: "pointer" }}>추가</button>
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

              {loading && (
                <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: 14 }}>
                  캐릭터 생성 중... 이미지 업로드 중...
                </div>
              )}

              <button onClick={handleSubmit} disabled={loading} style={{
                padding: "16px", borderRadius: 16, border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 700, fontSize: 16,
                opacity: loading ? 0.7 : 1,
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 0 30px rgba(139,124,255,.3)",
              }}>
                {loading ? "생성 중..." : "캐릭터 생성 완료"}
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}