const API_URL = 'http://localhost:8000';
const SESSION_ID = 'user_' + Math.random().toString(36).substr(2, 9);

let currentCharacter = null;
let characters = [];
let uploadedImageUrl = '';

function getAvatarColor(name) {
    const colors = ['#e94560', '#0f3460', '#533483', '#2b9348', '#e76f51'];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
}

async function loadCharacters() {
    const response = await fetch(`${API_URL}/characters`);
    characters = await response.json();

    const list = document.getElementById('characterList');
    list.innerHTML = '';

    characters.forEach(char => {
        const card = document.createElement('div');
        card.className = `character-card${char.custom ? ' custom' : ''}`;
        card.innerHTML = `
            <div class="character-avatar" style="${char.image_url ?
                `background-image:url(${API_URL + char.image_url}); background-size:cover; background-position:center` :
                `background:${getAvatarColor(char.name)}`}">
                ${char.image_url ? '' : char.name[0]}
            </div>
            <div class="character-info">
                <h2>
                    ${char.name}
                    ${char.custom ? '<span class="badge">내 캐릭터</span>' : ''}
                </h2>
                <p>${char.description || '클릭해서 대화 시작'}</p>
                ${char.category ? `<span class="category-tag">${char.category}</span>` : ''}
            </div>
        `;
        card.onclick = () => selectCharacter(char);
        list.appendChild(card);
    });
}

function selectCharacter(char) {
    currentCharacter = char;
    document.getElementById('characterName').textContent = char.name;
    document.getElementById('characterSelect').style.display = 'none';
    document.getElementById('chatContainer').style.display = 'flex';
    document.getElementById('chatMessages').innerHTML = '';

    if (char.situation) {
        const situationEl = document.createElement('div');
        situationEl.className = 'situation-box';
        situationEl.textContent = char.situation;
        document.getElementById('chatMessages').appendChild(situationEl);
    }

    if (char.first_message) {
        addMessage('assistant', char.first_message);
    }
}

function goBack() {
    currentCharacter = null;
    document.getElementById('characterSelect').style.display = 'block';
    document.getElementById('chatContainer').style.display = 'none';
}

function showCreateForm() {
    document.getElementById('characterSelect').style.display = 'none';
    document.getElementById('createForm').style.display = 'flex';
    uploadedImageUrl = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('imageUploadPlaceholder').style.display = 'flex';
    showTab('tab-profile');
}

function hideCreateForm() {
    document.getElementById('createForm').style.display = 'none';
    document.getElementById('characterSelect').style.display = 'block';
}

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    document.getElementById(tabId).style.display = 'block';
    document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
}

function selectCategory(el, value) {
    document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('selected'));
    el.classList.add('selected');
}

function selectVisibility(el, value) {
    document.querySelectorAll('.visibility-btn').forEach(b => b.classList.remove('selected'));
    el.classList.add('selected');
}

async function uploadImage(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload/image`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        uploadedImageUrl = data.image_url;

        const preview = document.getElementById('imagePreview');
        const placeholder = document.getElementById('imageUploadPlaceholder');
        preview.src = API_URL + uploadedImageUrl;
        preview.style.display = 'block';
        placeholder.style.display = 'none';
    } catch (e) {
        alert('이미지 업로드 실패');
    }
}

async function createCharacter() {
    const name = document.getElementById('charName').value.trim();
    const description = document.getElementById('charDescription').value.trim();
    const age = document.getElementById('charAge').value;
    const job = document.getElementById('charJob').value.trim();
    const personality = document.getElementById('charPersonality').value.trim();
    const likes = document.getElementById('charLikes').value.trim();
    const dislikes = document.getElementById('charDislikes').value.trim();
    const speech = document.getElementById('charSpeech').value.trim();
    const firstMessage = document.getElementById('charFirstMessage').value.trim();
    const situation = document.getElementById('charSituation').value.trim();
    const selectedCategory = document.querySelector('.category-btn.selected');
    const category = selectedCategory ? selectedCategory.textContent : '기타';
    const selectedVisibility = document.querySelector('.visibility-btn.selected');
    const visibility = selectedVisibility ? selectedVisibility.dataset.value : 'public';

    if (!name || !personality || !speech) {
        alert('이름, 성격, 말투는 필수예요!');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/characters`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                age: parseInt(age) || 20,
                job: job || '없음',
                personality,
                likes: likes || '없음',
                dislikes: dislikes || '없음',
                speech_style: speech,
                first_message: firstMessage,
                situation,
                category,
                visibility,
                image_url: uploadedImageUrl
            })
        });

        const data = await response.json();
        alert(`${data.name} 캐릭터가 생성됐어요!`);
        hideCreateForm();
        await loadCharacters();

    } catch (e) {
        alert('캐릭터 생성에 실패했어요.');
    }
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || !currentCharacter) return;

    input.value = '';
    addMessage('user', message);

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

async function clearChat() {
    await fetch(`${API_URL}/chat/${SESSION_ID}/${currentCharacter.id}`, {
        method: 'DELETE'
    });
    document.getElementById('chatMessages').innerHTML = '';

    if (currentCharacter.situation) {
        const situationEl = document.createElement('div');
        situationEl.className = 'situation-box';
        situationEl.textContent = currentCharacter.situation;
        document.getElementById('chatMessages').appendChild(situationEl);
    }

    if (currentCharacter.first_message) {
        addMessage('assistant', currentCharacter.first_message);
    }
}

function addMessage(role, content) {
    const messages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = content;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

function addTyping() {
    const messages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message assistant typing';
    div.textContent = '입력 중...';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

loadCharacters();