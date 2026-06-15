import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// 백엔드 API 서버 주소 및 세션 ID 세팅
const API_URL = 'http://localhost:8000';
const SESSION_ID = 'user_' + Math.random().toString(36).substr(2, 9);

function App() {
  // --- 상태 관리 (State) ---
  const [characters, setCharacters] = useState([]); // 백엔드에서 받아올 캐릭터 목록
  const [selectedChar, setSelectedChar] = useState(null); // 현재 선택된 대화 상대
  const [messages, setMessages] = useState([]); // 채팅 메시지 기록
  const [inputText, setInputText] = useState(""); // 입력창 텍스트
  const [isTyping, setIsTyping] = useState(false); // AI가 입력 중인지 여부
  
  // 캐릭터 만들기 모달/화면 상태 및 입력 폼 상태
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    name: '', description: '', age: '', job: '',
    personality: '', likes: '', dislikes: '', speech_style: '',
    situation: '', first_message: '', category: '기타', visibility: 'public'
  });
  const [uploadedImageUrl, setUploadedImageUrl] = useState('');

  const messagesEndRef = useRef(null); // 스크롤 제어용 Ref

  // --- 1. 이름 기반 아바타 배경색 자동 지정 ---
  const getAvatarColor = (name) => {
    const colors = ['#e94560', '#0f3460', '#533483', '#2b9348', '#e76f51'];
    const index = name ? name.charCodeAt(0) % colors.length : 0;
    return colors[index];
  };

  // --- 2. 백엔드에서 캐릭터 목록 가져오기 (API 연동) ---
  const loadCharacters = async () => {
    try {
      const response = await fetch(`${API_URL}/characters`);
      const data = await response.json();
      setCharacters(data);
    } catch (error) {
      console.error("캐릭터 목록 로드 실패:", error);
    }
  };

  // 컴포넌트가 처음 켜질 때 캐릭터 목록 로드
  useEffect(() => {
    loadCharacters();
  }, []);

  // 메시지가 추가될 때마다 채팅창 제일 아래로 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // --- 3. 캐릭터 선택 시 세팅 ---
  const handleSelectCharacter = (char) => {
    setSelectedChar(char);
    setMessages([]); // 기존 대화방 초기화
    
    // 시작 상황 박스 추가용 가상 메시지 구조 예시
    const initialMessages = [];
    if (char.first_message) {
      initialMessages.push({ id: 'first', sender: 'assistant', text: char.first_message });
    }
    setMessages(initialMessages);
  };

  // --- 4. 메시지 전송 (API 연동) ---
  const handleSendMessage = async () => {
    if (inputText.trim() === "" || !selectedChar) return;

    const userMsgText = inputText;
    setInputText(""); // 입력창 즉시 비우기

    // 1. 유저 메시지 화면에 먼저 추가
    const userMessage = { id: Date.now(), sender: 'user', text: userMsgText };
    setMessages(prev => [...prev, userMessage]);
    
    // 2. AI 입력 중 상태 켜기
    setIsTyping(true);

    try {
      // 3. 백엔드로 챗 요청 전송
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character_id: selectedChar.id,
          message: userMsgText,
          session_id: SESSION_ID
        })
      });
      
      const data = await response.json();
      
      // 4. AI 답변 화면에 추가
      setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'assistant', text: data.message }]);
    } catch (error) {
      setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'assistant', text: '오류가 발생했어. 다시 시도해줘.' }]);
    } finally {
      setIsTyping(false); // 입력 중 상태 끄기
    }
  };

  // --- 5. 대화방 초기화 (API 연동) ---
  const handleClearChat = async () => {
    if (!selectedChar) return;
    try {
      await fetch(`${API_URL}/chat/${SESSION_ID}/${selectedChar.id}`, { method: 'DELETE' });
      setMessages(selectedChar.first_message ? [{ id: 'first', sender: 'assistant', text: selectedChar.first_message }] : []);
    } catch (error) {
      alert("대화 초기화 실패");
    }
  };

  // --- 6. 이미지 업로드 (API 연동) ---
  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formDataObj = new FormData();
    formDataObj.append('file', file);

    try {
      const response = await fetch(`${API_URL}/upload/image`, {
        method: 'POST',
        body: formDataObj
      });
      const data = await response.json();
      setUploadedImageUrl(data.image_url);
    } catch (error) {
      alert("이미지 업로드 실패");
    }
  };

  // --- 7. 새 캐릭터 생성 제출 (API 연동) ---
  const handleCreateCharacter = async () => {
    const { name, personality, speech_style } = formData;
    if (!name || !personality || !speech_style) {
      alert('이름, 성격, 말투는 필수예요!');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/characters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          age: parseInt(formData.age) || 20,
          image_url: uploadedImageUrl
        })
      });

      const data = await response.json();
      alert(`${data.name} 캐릭터가 생성됐어요!`);
      
      // 폼 초기화 및 닫기
      setIsCreateOpen(false);
      setFormData({
        name: '', description: '', age: '', job: '',
        personality: '', likes: '', dislikes: '', speech_style: '',
        situation: '', first_message: '', category: '기타', visibility: 'public'
      });
      setUploadedImageUrl('');
      loadCharacters(); // 목록 리로드
    } catch (error) {
      alert('캐릭터 생성에 실패했어요.');
    }
  };

  return (
    <div className="app-container">
      {/* 메인 레이아웃: 캐릭터 선택이 안 되었으면 선택화면, 되었으면 채팅 화면 */}
      {!selectedChar ? (
        !isCreateOpen ? (
          /* 캐릭터 선택 화면 */
          <div className="character-select">
            <h1>누구와 대화할까요?</h1>
            <button className="create-btn" onClick={() => { setIsCreateOpen(true); setActiveTab('profile'); }}>+ 캐릭터 만들기</button>
            <div className="character-list">
              {characters.map(char => (
                <div key={char.id} className={`character-card ${char.custom ? 'custom' : ''}`} onClick={() => handleSelectCharacter(char)}>
                  <div className="character-avatar" style={char.image_url ? 
                    { backgroundImage: `url(${char.image_url.startsWith('http') ? char.image_url : API_URL + char.image_url})`, backgroundSize: 'cover', backgroundPosition: 'center' } : 
                    { background: getAvatarColor(char.name) }}>
                    {!char.image_url && char.name[0]}
                  </div>
                  <div className="character-info">
                    <h2>
                      {char.name}
                      {char.custom && <span className="badge">내 캐릭터</span>}
                    </h2>
                    <p>{char.description || '클릭해서 대화 시작'}</p>
                    {char.category && <span className="category-tag">{char.category}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* 캐릭터 만들기 화면 (멀티 탭 구조) */
          <div className="create-form">
            <div className="form-header">
              <button className="back-btn" onClick={() => setIsCreateOpen(false)}>← 뒤로</button>
              <span>캐릭터 만들기</span>
            </div>

            <div className="tab-bar">
              {['profile', 'detail', 'situation', 'setting'].map(tab => (
                <button key={tab} className={`tab-btn ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                  {tab === 'profile' && '프로필'}
                  {tab === 'detail' && '상세정보'}
                  {tab === 'situation' && '시작상황'}
                  {tab === 'setting' && '기타설정'}
                </button>
              ))}
            </div>

            <div className="form-body">
              {activeTab === 'profile' && (
                <>
                  <div className="form-group">
                    <label>캐릭터 이미지</label>
                    <div className="image-upload-area" onClick={() => document.getElementById('fileInput').click()}>
                      {uploadedImageUrl ? (
                        <img src={uploadedImageUrl.startsWith('http') ? uploadedImageUrl : API_URL + uploadedImageUrl} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '12px' }} />
                      ) : (
                        <div className="upload-placeholder">
                          <div style={{ fontSize: '32px' }}>📷</div>
                          <div style={{ fontSize: '13px', color: '#aaa', marginTop: '8px' }}>이미지 업로드</div>
                        </div>
                      )}
                    </div>
                    <input type="file" id="fileInput" accept="image/*" style={{ display: 'none' }} onChange={handleImageUpload} />
                  </div>
                  <div className="form-group">
                    <label>이름 *</label>
                    <input type="text" placeholder="캐릭터 이름을 입력해주세요" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>캐릭터 소개</label>
                    <textarea placeholder="캐릭터에 대한 소개를 간단하게 입력해주세요" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>나이</label>
                    <input type="number" placeholder="예: 22" value={formData.age} onChange={e => setFormData({...formData, age: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>직업</label>
                    <input type="text" placeholder="예: 대학생" value={formData.job} onChange={e => setFormData({...formData, job: e.target.value})} />
                  </div>
                  <button className="tab-next-btn" onClick={() => setActiveTab('detail')}>다음 단계 →</button>
                </>
              )}

              {activeTab === 'detail' && (
                <>
                  <div className="form-group">
                    <label>성격 *</label>
                    <textarea placeholder="성격을 입력해주세요" value={formData.personality} onChange={e => setFormData({...formData, personality: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>좋아하는 것</label>
                    <input type="text" placeholder="예: 카페, 드라마" value={formData.likes} onChange={e => setFormData({...formData, likes: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>싫어하는 것</label>
                    <input type="text" placeholder="예: 거짓말" value={formData.dislikes} onChange={e => setFormData({...formData, dislikes: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>말투 *</label>
                    <textarea placeholder="말투를 입력해주세요" value={formData.speech_style} onChange={e => setFormData({...formData, speech_style: e.target.value})} />
                  </div>
                  <button className="tab-next-btn" onClick={() => setActiveTab('situation')}>다음 단계 →</button>
                </>
              )}

              {activeTab === 'situation' && (
                <>
                  <div className="form-group">
                    <label>시작 상황</label>
                    <textarea placeholder="첫 만남 상황을 설정해주세요" value={formData.situation} onChange={e => setFormData({...formData, situation: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>첫 대사</label>
                    <textarea placeholder="캐릭터가 처음 건네는 말을 입력해주세요" value={formData.first_message} onChange={e => setFormData({...formData, first_message: e.target.value})} />
                  </div>
                  <button className="tab-next-btn" onClick={() => setActiveTab('setting')}>다음 단계 →</button>
                </>
              )}

              {activeTab === 'setting' && (
                <>
                  <div className="form-group">
                    <label>카테고리</label>
                    <div className="category-grid">
                      {['시뮬레이션', '로맨스', '판타지/SF', '드라마', '무협/사극', '코믹/일상', '공포/추리', '기타'].map(cat => (
                        <button key={cat} className={`category-btn ${formData.category === cat ? 'selected' : ''}`} onClick={() => setFormData({...formData, category: cat})}>{cat}</button>
                      ))}
                    </div>
                  </div>
                  <div className="form-group">
                    <label>공개 설정</label>
                    <div className="visibility-group">
                      <button className={`visibility-btn ${formData.visibility === 'public' ? 'selected' : ''}`} onClick={() => setFormData({...formData, visibility: 'public'})}>공개</button>
                      <button className={`visibility-btn ${formData.visibility === 'private' ? 'selected' : ''}`} onClick={() => setFormData({...formData, visibility: 'private'})}>비공개</button>
                    </div>
                  </div>
                  <button className="submit-btn" onClick={handleCreateCharacter}>캐릭터 생성 완료</button>
                </>
              )}
            </div>
          </div>
        )
      ) : (
        /* 채팅화면 활성화 */
        <div className="chat-container">
          <div className="chat-header">
            <button className="back-btn" onClick={() => setSelectedChar(null)}>← 뒤로</button>
            <span>{selectedChar.name}</span>
            <button className="clear-btn" onClick={handleClearChat}>초기화</button>
          </div>
          
          <div className="chat-messages">
            {selectedChar.situation && (
              <div className="situation-box">{selectedChar.situation}</div>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
            {isTyping && (
              <div className="message assistant typing">입력 중...</div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <input 
              type="text" 
              placeholder="메시지를 입력하세요..." 
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
            />
            <button onClick={handleSendMessage}>전송</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;