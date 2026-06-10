const API_URL = 'http://localhost:8000';
const SESSION_ID = 'user_' + Math.random().toString(36).substr(2, 9);

let currentCharacter = null;
let characters = [];

// 캐릭터 목록 불러오기
async function loadCharacters() {
    const response = await fetch(`${API_URL}/characters`);
    characters = await response.json();

    const list = document.getElementById('characterList');
    list.innerHTML = '';

    characters.forEach(char => {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.innerHTML = `
            <h2>${char.name}</h2>
            <p>클릭해서 대화 시작</p>
        `;
        card.onclick = () => selectCharacter(char);
        list.appendChild(card);
    });
}

// 캐릭터 선택
function selectCharacter(char) {
    currentCharacter = char;
    document.getElementById('characterName').textContent = char.name;
    document.getElementById('characterSelect').style.display = 'none';
    document.getElementById('chatContainer').style.display = 'flex';
    document.getElementById('chatMessages').innerHTML = '';

    addMessage('assistant', `안녕! 나 ${char.name}이야. 뭐가 궁금해?`);
}

// 뒤로가기
function goBack() {
    currentCharacter = null;
    document.getElementById('characterSelect').style.display = 'block';
    document.getElementById('chatContainer').style.display = 'none';
}

// 메시지 전송
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || !currentCharacter) return;

    input.value = '';
    addMessage('user', message);

    // 타이핑 표시
    const typingEl = addTyping();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_id: currentCharacter.id,
                message: message,
                session_id: SESSION_ID
            })
        });

        const data = await response.json();
        typingEl.remove();
        addMessage('assistant', data.message);
    } catch (e) {
        typingEl.remove();
        addMessage('assistant', '오류가 발생했어. 다시 시도해줘.');
    }
}

// 대화 초기화
async function clearChat() {
    await fetch(`${API_URL}/chat/${SESSION_ID}/${currentCharacter.id}`, {
        method: 'DELETE'
    });
    document.getElementById('chatMessages').innerHTML = '';
    addMessage('assistant', `대화가 초기화됐어. 다시 시작하자!`);
}

// 메시지 추가
function addMessage(role, content) {
    const messages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = content;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

// 타이핑 표시
function addTyping() {
    const messages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message assistant typing';
    div.textContent = '입력 중...';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

// 엔터키
function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

// 초기 로드
loadCharacters();