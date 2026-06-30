import { useState, useEffect, useRef } from "react";
import axios from "axios";
import type { Character, User } from "../App";

interface CommunityPageProps {
  apiUrl: string;
  token: string;
  user: User | null;
  onBack: () => void;
  onSelectCharacter: (char: Character) => void;
  onGoCreator: (userId: number) => void;
  onLoginRequired: () => void;
}

const POST_TYPES = [
  { key: "all", label: "전체" },
  { key: "general", label: "💬 일반" },
  { key: "party_recruit", label: "⚔ 파티 모집" },
  { key: "fanart", label: "🎨 팬아트" },
];

const GENRES = ["전체", "fantasy", "modern", "sf", "horror", "romance", "other"];
const GENRE_LABEL: Record<string, string> = {
  fantasy: "판타지", modern: "현대", sf: "SF",
  horror: "공포", romance: "로맨스", other: "기타"
};

export default function CommunityPage({
  apiUrl, token, user, onBack, onSelectCharacter, onGoCreator, onLoginRequired
}: CommunityPageProps) {
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [postType, setPostType] = useState("all");
  const [genre, setGenre] = useState("전체");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [showWriteModal, setShowWriteModal] = useState(false);
  const [selectedPost, setSelectedPost] = useState<any | null>(null);
  const observerRef = useRef<HTMLDivElement>(null);
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchPosts = async (reset = false) => {
    setLoading(true);
    const currentPage = reset ? 1 : page;
    try {
      const params = new URLSearchParams({
        page: String(currentPage),
        limit: "20",
      });
      if (postType !== "all") params.append("post_type", postType);
      if (genre !== "전체") params.append("genre", genre);

      const res = await axios.get(`${apiUrl}/community?${params}`, { headers });
      if (reset) {
        setPosts(res.data);
        setPage(2);
      } else {
        if (res.data.length === 0) {
          setHasMore(false);
        } else {
          setPosts(prev => [...prev, ...res.data]);
          setPage(prev => prev + 1);
        }
      }
    } catch {
      console.error("피드 로드 실패");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setHasMore(true);
    fetchPosts(true);
  }, [postType, genre]);

  useEffect(() => {
    if (!observerRef.current) return;
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading && posts.length > 0) {
          fetchPosts();
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [postType, genre]);

  const handleLike = async (postId: number) => {
    if (!token) { onLoginRequired(); return; }
    try {
      const res = await axios.post(`${apiUrl}/community/${postId}/like`, {}, { headers });
      setPosts(prev => prev.map(p =>
        p.id === postId
          ? { ...p, is_liked: res.data.liked, like_count: res.data.like_count }
          : p
      ));
    } catch { console.error("좋아요 실패"); }
  };

  return (
    <div style={{ minHeight: "100vh", height: "100vh", overflowY: "auto", position: "relative", zIndex: 2 }}>

      {/* 네비 */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 10,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "16px 32px",
        background: "rgba(9,11,20,.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button onClick={onBack} style={{
            width: 40, height: 40, borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(24,29,54,.75)",
            color: "var(--text-secondary)", fontSize: 18, cursor: "pointer",
          }}>←</button>
          <div style={{
            fontSize: 22, fontWeight: 800,
            background: "var(--gradient-cosmic)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>커뮤니티</div>
        </div>

        {token && (
          <button onClick={() => setShowWriteModal(true)} style={{
            padding: "10px 20px", borderRadius: 12,
            border: "none",
            background: "var(--gradient-cosmic)",
            color: "#fff", fontWeight: 700, fontSize: 14, cursor: "pointer",
          }}>+ 글쓰기</button>
        )}
      </nav>

      {/* 필터 */}
      <div style={{
        padding: "12px 32px", display: "flex", gap: 8, flexWrap: "wrap",
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(9,11,20,.6)",
      }}>
        {POST_TYPES.map(t => (
          <button key={t.key} onClick={() => setPostType(t.key)} style={{
            padding: "7px 16px", borderRadius: 999, fontSize: 13,
            border: postType === t.key ? "none" : "1px solid var(--border-default)",
            background: postType === t.key ? "var(--gradient-cosmic)" : "rgba(255,255,255,.04)",
            color: postType === t.key ? "#fff" : "var(--text-muted)",
            fontWeight: 600, cursor: "pointer", transition: "all .2s ease",
          }}>{t.label}</button>
        ))}

        <div style={{ width: 1, background: "var(--border-subtle)", margin: "0 4px" }} />

        {GENRES.map(g => (
          <button key={g} onClick={() => setGenre(g)} style={{
            padding: "7px 16px", borderRadius: 999, fontSize: 13,
            border: genre === g ? "none" : "1px solid var(--border-default)",
            background: genre === g ? "rgba(139,124,255,.3)" : "rgba(255,255,255,.04)",
            color: genre === g ? "#fff" : "var(--text-muted)",
            fontWeight: 600, cursor: "pointer", transition: "all .2s ease",
          }}>{g === "전체" ? g : GENRE_LABEL[g]}</button>
        ))}
      </div>

      {/* 피드 */}
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px", display: "flex", flexDirection: "column", gap: 16 }}>
        {posts.map(post => (
          <PostCard
            key={post.id}
            post={post}
            onLike={() => handleLike(post.id)}
            onClick={() => setSelectedPost(post)}
            onGoCreator={onGoCreator}
          />
        ))}

        <div ref={observerRef} style={{ height: 40, display: "flex", alignItems: "center", justifyContent: "center" }}>
          {loading && <div style={{ color: "var(--text-muted)", fontSize: 13 }}>불러오는 중...</div>}
          {!hasMore && posts.length > 0 && (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>모든 게시글을 불러왔어요.</div>
          )}
          {!loading && posts.length === 0 && (
            <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "60px 0" }}>게시글이 없어요.</div>
          )}
        </div>
      </div>

      {/* 글쓰기 모달 */}
      {showWriteModal && (
        <WritePostModal
          apiUrl={apiUrl}
          headers={headers}
          onClose={() => setShowWriteModal(false)}
          onPosted={() => { setShowWriteModal(false); fetchPosts(true); }}
        />
      )}

      {/* 게시글 상세 모달 */}
      {selectedPost && (
        <PostDetailModal
          post={selectedPost}
          apiUrl={apiUrl}
          token={token}
          headers={headers}
          user={user}
          onClose={() => setSelectedPost(null)}
          onLike={() => handleLike(selectedPost.id)}
          onGoCreator={onGoCreator}
          onDeleted={() => fetchPosts(true)}
        />
      )}
    </div>
  );
}

// ── PostCard ─────────────────────────────────────────────────
function PostCard({ post, onLike, onClick, onGoCreator }: {
  post: any; onLike: () => void; onClick: () => void; onGoCreator: (id: number) => void;
}) {
  return (
    <div onClick={onClick} style={{
      borderRadius: 20, padding: 20,
      border: "1px solid var(--border-default)",
      background: "rgba(17,21,40,.7)",
      backdropFilter: "blur(16px)",
      cursor: "pointer", transition: "all .2s ease",
    }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(139,124,255,.4)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 20px rgba(139,124,255,.1)";
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-default)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "none";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}
        onClick={e => { e.stopPropagation(); onGoCreator(post.user_id); }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          background: "var(--gradient-cosmic)",
          display: "grid", placeItems: "center",
          fontWeight: 700, fontSize: 14, flexShrink: 0,
          overflow: "hidden",
        }}>
          {post.profile_image_url
            ? <img src={post.profile_image_url} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : post.username?.[0]?.toUpperCase()}
        </div>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
            {post.equipped_prefix && <span style={{ color: "var(--primary)", marginRight: 4 }}>{post.equipped_prefix}</span>}
            {post.username}
            {post.equipped_suffix && <span style={{ color: "var(--secondary)", marginLeft: 4 }}>{post.equipped_suffix}</span>}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {new Date(post.created_at).toLocaleDateString("ko-KR")}
            {post.genre && <span style={{ marginLeft: 8, color: "var(--primary)" }}>#{GENRE_LABEL[post.genre] ?? post.genre}</span>}
          </div>
        </div>

        <div style={{ marginLeft: "auto" }}>
          {post.post_type === "party_recruit" && (
            <span style={{
              padding: "3px 10px", borderRadius: 999, fontSize: 11,
              background: "rgba(139,124,255,.2)", border: "1px solid rgba(139,124,255,.3)",
              color: "var(--primary)", fontWeight: 600,
            }}>⚔ 파티 모집</span>
          )}
          {post.post_type === "fanart" && (
            <span style={{
              padding: "3px 10px", borderRadius: 999, fontSize: 11,
              background: "rgba(255,120,180,.12)", border: "1px solid rgba(255,120,180,.3)",
              color: "#ff78b4", fontWeight: 600,
            }}>🎨 팬아트</span>
          )}
        </div>
      </div>

      {post.title && (
        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8, color: "var(--text-primary)" }}>
          {post.title}
        </div>
      )}

      <div style={{
        color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.6,
        overflow: "hidden", display: "-webkit-box",
        WebkitLineClamp: 3, WebkitBoxOrient: "vertical",
        marginBottom: post.image_url ? 12 : 0,
      }}>{post.content}</div>

      {post.ai_description && (
        <div style={{
          marginTop: 8, padding: "8px 12px", borderRadius: 10,
          background: "rgba(139,124,255,.06)",
          border: "1px solid rgba(139,124,255,.12)",
          color: "var(--text-muted)", fontSize: 12, lineHeight: 1.5,
        }}>✦ {post.ai_description}</div>
      )}

      {post.image_url && (
        <img src={`${post.image_url}`} alt="게시글 이미지"
          style={{ width: "100%", borderRadius: 12, marginTop: 12, objectFit: "cover", maxHeight: 300 }} />
      )}

      {post.character_tags?.length > 0 && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
          {post.character_tags.map((c: any) => (
            <span key={c.id} style={{
              padding: "4px 10px", borderRadius: 999, fontSize: 12,
              background: "rgba(95,214,255,.08)", border: "1px solid rgba(95,214,255,.2)",
              color: "var(--secondary)", fontWeight: 600,
            }}>@ {c.name}</span>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 16, marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--border-subtle)" }}>
        <button onClick={e => { e.stopPropagation(); onLike(); }} style={{
          display: "flex", alignItems: "center", gap: 6,
          background: "none", border: "none",
          color: post.is_liked ? "#ff6b8a" : "var(--text-muted)",
          fontSize: 13, cursor: "pointer", fontWeight: 600,
        }}>♥ {post.like_count ?? 0}</button>
        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>💬 {post.comment_count ?? 0}</span>
        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>👁 {post.view_count ?? 0}</span>
      </div>
    </div>
  );
}

// ── WritePostModal ────────────────────────────────────────────
function WritePostModal({ apiUrl, headers, onClose, onPosted }: {
  apiUrl: string; headers: any; onClose: () => void; onPosted: () => void;
}) {
  const [postType, setPostType] = useState("general");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [characterSearch, setCharacterSearch] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [taggedChars, setTaggedChars] = useState<any[]>([]);
  const [partyMax, setPartyMax] = useState(4);
  const [submitting, setSubmitting] = useState(false);
  const [aiResult, setAiResult] = useState<{ genre: string; description: string } | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!["image/jpeg", "image/png", "image/gif", "image/webp"].includes(file.type)) {
      alert("JPG, PNG, GIF, WEBP 파일만 업로드 가능해요.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("파일 크기는 10MB 이하여야 해요.");
      return;
    }

    setImage(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleCharSearch = async (q: string) => {
    setCharacterSearch(q);
    if (!q.trim()) { setSearchResults([]); return; }
    try {
      const res = await axios.get(`${apiUrl}/characters/search?q=${encodeURIComponent(q)}`, { headers });
      setSearchResults(res.data.slice(0, 5));
    } catch { console.error(); }
  };

  const handleTagChar = (char: any) => {
    if (taggedChars.find(c => c.id === char.id)) return;
    setTaggedChars(prev => [...prev, char]);
    setCharacterSearch("");
    setSearchResults([]);
  };

  const handleSubmit = async () => {
    if (submitting) return;
    if (!content.trim()) { alert("내용을 입력해주세요."); return; }
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("content", content.trim());
      formData.append("post_type", postType);
      if (title.trim()) formData.append("title", title.trim());
      if (taggedChars.length > 0) formData.append("character_ids", taggedChars.map(c => c.id).join(","));
      if (postType === "party_recruit") formData.append("party_max", String(partyMax));
      if (image) formData.append("image", image);

      const res = await axios.post(`${apiUrl}/community`, formData, {
        headers: { ...headers, "Content-Type": "multipart/form-data" }
      });

      if (res.data.genre || res.data.ai_description) {
        setAiResult({ genre: res.data.genre, description: res.data.ai_description });
        setTimeout(() => onPosted(), 1500);
      } else {
        onPosted();
      }
    } catch {
      alert("게시글 작성에 실패했어요.");
      setSubmitting(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.75)", display: "grid", placeItems: "center", zIndex: 200 }}>
      <div style={{
        width: "min(560px, 95vw)", maxHeight: "90vh", overflowY: "auto",
        borderRadius: 24, padding: 28,
        background: "rgba(17,21,40,.98)",
        border: "1px solid var(--border-default)",
        display: "flex", flexDirection: "column", gap: 16,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontWeight: 700, fontSize: 18 }}>게시글 작성</div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 22, cursor: "pointer" }}>×</button>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {POST_TYPES.filter(t => t.key !== "all").map(t => (
            <button key={t.key} onClick={() => setPostType(t.key)} style={{
              padding: "7px 14px", borderRadius: 999, fontSize: 13,
              border: postType === t.key ? "none" : "1px solid var(--border-default)",
              background: postType === t.key ? "var(--gradient-cosmic)" : "rgba(255,255,255,.04)",
              color: postType === t.key ? "#fff" : "var(--text-muted)",
              fontWeight: 600, cursor: "pointer",
            }}>{t.label}</button>
          ))}
        </div>

        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="제목 (선택)"
          maxLength={100}
          style={{
            padding: "12px 16px", borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-primary)", fontSize: 14, outline: "none",
          }}
        />

        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="내용을 입력해주세요..."
          maxLength={2000}
          rows={5}
          style={{
            padding: "12px 16px", borderRadius: 12,
            border: "1px solid var(--border-default)",
            background: "rgba(255,255,255,.04)",
            color: "var(--text-primary)", fontSize: 14,
            outline: "none", resize: "vertical", lineHeight: 1.6,
          }}
        />

        {postType === "party_recruit" && (
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ color: "var(--text-muted)", fontSize: 14 }}>최대 인원</span>
            {[2, 3, 4, 5, 6].map(n => (
              <button key={n} onClick={() => setPartyMax(n)} style={{
                width: 36, height: 36, borderRadius: 10,
                border: partyMax === n ? "none" : "1px solid var(--border-default)",
                background: partyMax === n ? "var(--gradient-cosmic)" : "rgba(255,255,255,.04)",
                color: partyMax === n ? "#fff" : "var(--text-muted)",
                fontWeight: 700, cursor: "pointer",
              }}>{n}</button>
            ))}
          </div>
        )}

        <div style={{ position: "relative" }}>
          <input
            value={characterSearch}
            onChange={e => handleCharSearch(e.target.value)}
            placeholder="@ 캐릭터 태그 검색..."
            style={{
              width: "100%", padding: "10px 16px", borderRadius: 12,
              border: "1px solid var(--border-default)",
              background: "rgba(255,255,255,.04)",
              color: "var(--text-primary)", fontSize: 14, outline: "none",
              boxSizing: "border-box",
            }}
          />
          {searchResults.length > 0 && (
            <div style={{
              position: "absolute", top: "100%", left: 0, right: 0, zIndex: 10,
              background: "rgba(17,21,40,.98)", border: "1px solid var(--border-default)",
              borderRadius: 12, overflow: "hidden", marginTop: 4,
            }}>
              {searchResults.map(c => (
                <div key={c.id} onClick={() => handleTagChar(c)} style={{
                  padding: "10px 16px", cursor: "pointer", fontSize: 14,
                  display: "flex", alignItems: "center", gap: 10,
                  transition: "background .15s",
                }}
                  onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.background = "rgba(139,124,255,.1)"}
                  onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.background = "transparent"}
                >
                  {c.image_url && <img src={c.image_url} style={{ width: 28, height: 28, borderRadius: "50%", objectFit: "cover" }} />}
                  <span>{c.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {taggedChars.length > 0 && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {taggedChars.map(c => (
              <span key={c.id} style={{
                padding: "4px 10px", borderRadius: 999, fontSize: 12,
                background: "rgba(95,214,255,.1)", border: "1px solid rgba(95,214,255,.25)",
                color: "var(--secondary)", display: "flex", alignItems: "center", gap: 6,
              }}>
                @ {c.name}
                <span onClick={() => setTaggedChars(prev => prev.filter(x => x.id !== c.id))}
                  style={{ cursor: "pointer", opacity: .6 }}>×</span>
              </span>
            ))}
          </div>
        )}

        <label style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "10px 16px", borderRadius: 12,
          border: "1px dashed var(--border-default)",
          cursor: "pointer", color: "var(--text-muted)", fontSize: 13,
        }}>
          🖼 이미지 첨부 (JPG/PNG/GIF, 10MB 이하)
          <input type="file" accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={handleImageChange} style={{ display: "none" }} />
        </label>

        {imagePreview && (
          <div style={{ position: "relative" }}>
            <img src={imagePreview} style={{ width: "100%", borderRadius: 12, maxHeight: 200, objectFit: "cover" }} />
            <button onClick={() => { setImage(null); setImagePreview(null); }} style={{
              position: "absolute", top: 8, right: 8,
              width: 28, height: 28, borderRadius: "50%",
              background: "rgba(0,0,0,.6)", border: "none",
              color: "#fff", cursor: "pointer", fontSize: 16,
            }}>×</button>
          </div>
        )}

        {aiResult && (
          <div style={{
            padding: "12px 16px", borderRadius: 12,
            background: "rgba(139,124,255,.08)",
            border: "1px solid rgba(139,124,255,.2)",
            color: "var(--text-secondary)", fontSize: 13,
          }}>
            ✦ AI 분류: <strong>{GENRE_LABEL[aiResult.genre] ?? aiResult.genre}</strong>
            {aiResult.description && <div style={{ marginTop: 4, color: "var(--text-muted)" }}>{aiResult.description}</div>}
          </div>
        )}

        <button onClick={handleSubmit} disabled={submitting} style={{
          padding: "14px", borderRadius: 14, border: "none",
          background: submitting ? "rgba(139,124,255,.3)" : "var(--gradient-cosmic)",
          color: "#fff", fontWeight: 700, fontSize: 15, cursor: submitting ? "not-allowed" : "pointer",
        }}>{submitting ? "업로드 중..." : "게시하기"}</button>
      </div>
    </div>
  );
}

// ── PostDetailModal ───────────────────────────────────────────
function PostDetailModal({ post, apiUrl, token, headers, user, onClose, onLike, onGoCreator, onDeleted }: {
  post: any; apiUrl: string; token: string; headers: any;
  user: any; onClose: () => void; onLike: () => void; onGoCreator: (id: number) => void;
  onDeleted: () => void;
}) {
  const [comments, setComments] = useState<any[]>([]);
  const [commentText, setCommentText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [viewCount, setViewCount] = useState(post.view_count ?? 0);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(post.title || "");
  const [editContent, setEditContent] = useState(post.content || "");
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [displayTitle, setDisplayTitle] = useState(post.title);
  const [displayContent, setDisplayContent] = useState(post.content);

  useEffect(() => {
    axios.get(`${apiUrl}/community/${post.id}`, { headers })
      .then(res => {
        setComments(res.data.comments ?? []);
        setViewCount(res.data.view_count ?? 0);
      })
      .catch(console.error);
  }, [post.id]);

  const handleComment = async () => {
    if (!commentText.trim() || !token) return;
    setSubmitting(true);
    try {
      await axios.post(`${apiUrl}/community/${post.id}/comments`,
        { content: commentText.trim() }, { headers });
      setCommentText("");
      const res = await axios.get(`${apiUrl}/community/${post.id}`, { headers });
      setComments(res.data.comments ?? []);
    } catch { alert("댓글 작성 실패"); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    if (!confirm("정말 삭제할까요?")) return;
    try {
      await axios.delete(`${apiUrl}/community/${post.id}`, { headers });
      onDeleted();
      onClose();
    } catch { alert("삭제 실패"); }
  };

  const handleEdit = async () => {
    if (!editContent.trim()) { alert("내용을 입력해주세요."); return; }
    setEditSubmitting(true);
    try {
      await axios.put(`${apiUrl}/community/${post.id}`,
        { title: editTitle.trim(), content: editContent.trim() },
        { headers }
      );
      setDisplayTitle(editTitle.trim());
      setDisplayContent(editContent.trim());
      setIsEditing(false);
      onDeleted();
    } catch { alert("수정 실패"); }
    finally { setEditSubmitting(false); }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.75)", display: "grid", placeItems: "center", zIndex: 200 }}>
      <div style={{
        width: "min(600px, 95vw)", maxHeight: "90vh", overflowY: "auto",
        borderRadius: 24, padding: 28,
        background: "rgba(17,21,40,.98)",
        border: "1px solid var(--border-default)",
        display: "flex", flexDirection: "column", gap: 16,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontWeight: 700, fontSize: 16 }}>{displayTitle || "게시글"}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {user?.id === post.user_id && !isEditing && (
              <>
                <button onClick={() => setIsEditing(true)} style={{
                  background: "none", border: "none",
                  color: "var(--primary)", fontSize: 13, cursor: "pointer", fontWeight: 600,
                }}>수정</button>
                <button onClick={handleDelete} style={{
                  background: "none", border: "none",
                  color: "#ff6b8a", fontSize: 13, cursor: "pointer", fontWeight: 600,
                }}>삭제</button>
              </>
            )}
            <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: 22, cursor: "pointer" }}>×</button>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}
            onClick={() => { onClose(); onGoCreator(post.user_id); }}>
            <div style={{
              width: 36, height: 36, borderRadius: "50%",
              background: "var(--gradient-cosmic)",
              display: "grid", placeItems: "center", fontWeight: 700, overflow: "hidden",
            }}>
              {post.profile_image_url
                ? <img src={post.profile_image_url} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                : post.username?.[0]?.toUpperCase()}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{post.username}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {new Date(post.created_at).toLocaleString("ko-KR")}
              </div>
            </div>
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 12 }}>👁 {viewCount}</div>
        </div>

        {isEditing ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <input
              value={editTitle}
              onChange={e => setEditTitle(e.target.value)}
              placeholder="제목 (선택)"
              style={{
                padding: "10px 14px", borderRadius: 10,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.04)",
                color: "var(--text-primary)", fontSize: 14, outline: "none",
              }}
            />
            <textarea
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              rows={5}
              style={{
                padding: "10px 14px", borderRadius: 10,
                border: "1px solid var(--border-default)",
                background: "rgba(255,255,255,.04)",
                color: "var(--text-primary)", fontSize: 14,
                outline: "none", resize: "vertical", lineHeight: 1.6,
              }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => setIsEditing(false)} style={{
                flex: 1, padding: "10px", borderRadius: 10,
                border: "1px solid var(--border-default)",
                background: "none", color: "var(--text-muted)", cursor: "pointer",
              }}>취소</button>
              <button onClick={handleEdit} disabled={editSubmitting} style={{
                flex: 1, padding: "10px", borderRadius: 10, border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 600, cursor: "pointer",
              }}>{editSubmitting ? "저장 중..." : "저장"}</button>
            </div>
          </div>
        ) : (
          <div style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.7 }}>{displayContent}</div>
        )}

        {post.image_url && (
          <img src={post.image_url} style={{ width: "100%", borderRadius: 12, objectFit: "cover", maxHeight: 400 }} />
        )}

        {post.character_tags?.length > 0 && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {post.character_tags.map((c: any) => (
              <span key={c.id} style={{
                padding: "4px 10px", borderRadius: 999, fontSize: 12,
                background: "rgba(95,214,255,.08)", border: "1px solid rgba(95,214,255,.2)",
                color: "var(--secondary)", fontWeight: 600,
              }}>@ {c.name}</span>
            ))}
          </div>
        )}

        <button onClick={onLike} style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "10px 20px", borderRadius: 12, width: "fit-content",
          border: `1px solid ${post.is_liked ? "rgba(255,107,138,.4)" : "var(--border-default)"}`,
          background: post.is_liked ? "rgba(255,107,138,.1)" : "rgba(255,255,255,.04)",
          color: post.is_liked ? "#ff6b8a" : "var(--text-muted)",
          fontWeight: 600, cursor: "pointer",
        }}>♥ {post.like_count ?? 0}</button>

        <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 12 }}>댓글 {comments.length}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
            {comments.map(c => (
              <div key={c.id} style={{ display: "flex", gap: 10 }}>
                <div style={{
                  width: 30, height: 30, borderRadius: "50%", flexShrink: 0,
                  background: "var(--gradient-cosmic)",
                  display: "grid", placeItems: "center", fontSize: 12, fontWeight: 700,
                }}>{c.username?.[0]?.toUpperCase()}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{c.username}</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>{c.content}</div>
                </div>
              </div>
            ))}
          </div>

          {token && (
            <div style={{ display: "flex", gap: 10 }}>
              <input
                value={commentText}
                onChange={e => setCommentText(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleComment()}
                placeholder="댓글 작성..."
                style={{
                  flex: 1, padding: "10px 14px", borderRadius: 12,
                  border: "1px solid var(--border-default)",
                  background: "rgba(255,255,255,.04)",
                  color: "var(--text-primary)", fontSize: 13, outline: "none",
                }}
              />
              <button onClick={handleComment} disabled={submitting} style={{
                padding: "10px 18px", borderRadius: 12, border: "none",
                background: "var(--gradient-cosmic)",
                color: "#fff", fontWeight: 600, cursor: "pointer",
              }}>전송</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}