// src/App.tsx
import { useState, useEffect } from 'react';
import axios from 'axios';

const TEMPORARY_SESSION_ID = "my_awesome_chat_session_2026";

function App() {
  // 1. 인증 관련 상태
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // 2. 서비스 기능 관련 상태
  const [characters, setCharacters] = useState<any[]>([]);
  const [selectedChar, setSelectedChar] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);

  // 캐릭터 목록 가져오기
  useEffect(() => {
    axios.get('http://localhost:8000/characters')
      .then(res => setCharacters(res.data))
      .catch(err => console.error('캐릭터 로드 실패:', err));
  }, [token]);

  // 🛡️ FastAPI Form Data 규격 유효성 검증을 통과하는 통합 인증 처리 함수
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    
    const endpoint = isRegisterMode 
      ? 'http://localhost:8000/auth/register' 
      : 'http://localhost:8000/auth/login';

    try {
      // 💡 FastAPI의 Field Required (422) 에러를 해결하기 위해 application/x-www-form-urlencoded 포맷으로 변환
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log("➡️ 백엔드 응답 데이터 성공:", response.data);

      if (isRegisterMode) {
        alert('회원가입 성공! 로그인해 주세요.');
        setIsRegisterMode(false);
        setUsername(''); 
        setPassword('');
      } else {
        const accessToken = response.data?.access_token;
        if (accessToken) {
          localStorage.setItem('token', accessToken);
          setToken(accessToken);
          setUsername('');
          setPassword('');
          alert('로그인 성공! 이제 인증된 상태로 대화합니다.');
        } else {
          setAuthError('백엔드에서 토큰(access_token)을 내려주지 않았거나 Key 이름이 다릅니다.');
        }
      }
    } catch (err: any) {
      console.error("❌ 인증 요청 에러 상세:", err);
      
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' 
        ? JSON.stringify(errorDetail) 
        : errorDetail;

      setAuthError(errorMessage || '백엔드 서버 연동 실패 (주소 에러 혹은 CORS 에러)');
    }
  };

  // 🔓 로그아웃 함수
  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setSelectedChar(null);
    setMessages([]);
    alert('로그아웃 되었습니다.');
  };

  // 💬 메시지 전송 함수
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userText = input;
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setInput('');
    setIsSending(true);

    try {
      // 로컬스토리지에 JWT 토큰이 있으면 Authorization 헤더에 Bearer 토큰 탑재
      const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};

      const response = await axios.post('http://localhost:8000/chat', {
        character_id: String(selectedChar.id || selectedChar._id),
        message: userText,
        session_id: TEMPORARY_SESSION_ID
      }, config);

      const aiResponseText = response.data.message;
      setMessages(prev => [...prev, { role: 'assistant', content: aiResponseText }]);
    } catch (err) {
      console.error('채팅 전송 실패:', err);
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ AI가 응답에 실패했습니다.' }]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      
      {/* 최상단 인증 제어 바 */}
      <div style={{ border: '1px dashed #007bff', padding: '15px', borderRadius: '8px', marginBottom: '30px', backgroundColor: '#f0f7ff' }}>
        {token ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#0056b3', fontWeight: 'bold' }}>🔓 현재 상태: 로그인 됨 (JWT 토큰 탑재 완료)</span>
            <button onClick={handleLogout} style={{ padding: '6px 12px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>로그아웃</button>
          </div>
        ) : (
          <div>
            <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>🔑 {isRegisterMode ? '회원가입 테스트' : '로그인 테스트 (미인증 상태)'}</h4>
            {authError && <div style={{ color: 'red', fontSize: '12px', whiteSpace: 'pre-wrap', marginBottom: '8px' }}>⚠️ {authError}</div>}
            <form onSubmit={handleAuth} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <input type="text" placeholder="아이디" value={username} onChange={(e) => setUsername(e.target.value)} required style={{ padding: '6px', width: '120px' }} />
              <input type="password" placeholder="비밀번호" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ padding: '6px', width: '120px' }} />
              <button type="submit" style={{ padding: '6px 12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                {isRegisterMode ? '가입' : '로그인'}
              </button>
              <button type="button" onClick={() => { setIsRegisterMode(!isRegisterMode); setAuthError(null); }} style={{ background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', textDecoration: 'underline', fontSize: '12px' }}>
                {isRegisterMode ? '로그인으로' : '회원가입으로'}
              </button>
            </form>
          </div>
        )}
      </div>

      {/* 캐릭터 선택 및 대화창 */}
      <h1>🤖 AI 캐릭터 챗봇 앱</h1>
      <hr style={{ border: '1px solid #ddd', marginBottom: '25px' }} />

      {!selectedChar ? (
        <div>
          <h2>👤 대화할 캐릭터를 선택하세요</h2>
          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            {characters.map((char: any) => (
              <div key={char.id || char._id} style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', width: '200px', backgroundColor: '#f9f9f9' }}>
                <h3>{char.name}</h3>
                <p style={{ fontSize: '13px', color: '#666' }}>{char.description || '설명이 없습니다.'}</p>
                <button onClick={() => setSelectedChar(char)} style={{ width: '100%', padding: '8px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                  💬 대화하기
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h2>💬 {selectedChar.name}님과의 대화</h2>
            <button onClick={() => { setSelectedChar(null); setMessages([]); }} style={{ cursor: 'pointer', padding: '6px 12px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px' }}>
              ⬅️ 나가기
            </button>
          </div>

          <div style={{ border: '1px solid #e1e1e3', height: '300px', borderRadius: '8px', padding: '15px', overflowY: 'auto', backgroundColor: '#f8f9fa', marginBottom: '15px' }}>
            {messages.length === 0 && <p style={{ color: '#999', textAlign: 'center', marginTop: '120px' }}>대화를 시작해 보세요!</p>}
            {messages.map((msg, index) => (
              <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '12px 0' }}>
                <span style={{ display: 'inline-block', padding: '10px 14px', borderRadius: '12px', backgroundColor: msg.role === 'user' ? '#007bff' : '#ffffff', color: msg.role === 'user' ? 'white' : '#212529', maxWidth: '75%', boxShadow: '0 1px 3px rgba(0,0,0,0.08)', border: msg.role === 'user' ? 'none' : '1px solid #e1e1e3' }}>
                  {msg.content}
                </span>
              </div>
            ))}
            {isSending && <p style={{ color: '#6c757d', fontSize: '13px' }}>⚡ 답변 생성 중...</p>}
          </div>

          <form onSubmit={sendMessage} style={{ display: 'flex', gap: '10px' }}>
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder={`${selectedChar.name}에게 보낼 메시지...`} disabled={isSending} style={{ flex: 1, padding: '12px', borderRadius: '6px', border: '1px solid #ccc' }} />
            <button type="submit" disabled={isSending || !input.trim()} style={{ padding: '0 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>전송</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;