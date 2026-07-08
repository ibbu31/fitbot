let selectedImage = null;
let voiceEnabled = false;
let guestMessageCount = parseInt(localStorage.getItem('fitbot_guest_msgs') || '0');

// ==================
// SEND MESSAGE
// ==================
function sendMessage() {
    const input = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const message = input.value.trim();

    if (!message && !selectedImage) return;

    // Guest message limit check
    if (IS_GUEST) {
        if (guestMessageCount >= MAX_GUEST_MESSAGES) {
            showSignupPopup();
            return;
        }
        guestMessageCount++;
        localStorage.setItem('fitbot_guest_msgs', guestMessageCount);
        updateGuestCounter();
    }

    if (message) {
        chatBox.innerHTML += `
            <div class="message user-message">
                <div class="message-content">${message}</div>
            </div>`;
    }

    let imagePayload = selectedImage;
    if (selectedImage) {
        chatBox.innerHTML += `
            <div class="message user-message">
                <div class="message-content">
                    <img src="${selectedImage}" class="user-image"/>
                </div>
            </div>`;
    }

    input.value = '';
    clearImage();

    chatBox.innerHTML += `<div class="typing" id="typing">FitBot is thinking... 💭</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    const selectedLang = document.getElementById('lang-select') ?
        document.getElementById('lang-select').value : 'en-US';

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message || "I am sending you an image",
            image: imagePayload,
            language: selectedLang,
            is_guest: IS_GUEST
        })
    })
    .then(response => response.json())
    .then(data => {
        const typingEl = document.getElementById('typing');
        if (typingEl) typingEl.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot-message';
        msgDiv.innerHTML = `
            <div class="bot-avatar">F</div>
            <div class="message-content">${formatMessage(data.reply)}</div>`;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        if (voiceEnabled && !IS_GUEST) speakText(data.reply);

        // Show signup popup after last free message
        if (IS_GUEST && guestMessageCount >= MAX_GUEST_MESSAGES) {
            setTimeout(() => showSignupPopup(), 2000);
        }
    })
    .catch(error => {
        const typingEl = document.getElementById('typing');
        if (typingEl) typingEl.remove();
        chatBox.innerHTML += `
            <div class="message bot-message">
                <div class="bot-avatar">F</div>
                <div class="message-content">❌ Something went wrong. Please try again!</div>
            </div>`;
    });
}

// Update guest counter display
function updateGuestCounter() {
    const el = document.getElementById('msgs-left');
    if (el) {
        const left = Math.max(0, MAX_GUEST_MESSAGES - guestMessageCount);
        el.textContent = left;
        if (left === 0) {
            el.style.color = '#ff4444';
        } else if (left === 1) {
            el.style.color = '#f59e0b';
        }
    }
}

// ==================
// SIGNUP POPUP
// ==================
function showSignupPopup() {
    document.getElementById('signup-modal').classList.add('open');
}

function closeSignupPopup() {
    document.getElementById('signup-modal').classList.remove('open');
}

// Quick message from feature cards
function sendQuickMessage(message) {
    document.getElementById('user-input').value = message;
    sendMessage();
}

// ==================
// FORMAT MESSAGE
// ==================
function formatMessage(text) {
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/^[•\-]\s(.+)/gm, '<li>$1</li>');
    text = text.replace(/(<li>[\s\S]*?<\/li>\n?)+/g, function(match) {
        return '<ul style="padding-left:16px;margin:6px 0;">' + match + '</ul>';
    });
    text = text.replace(/^\d+\.\s(.+)/gm, '<li>$1</li>');
    text = text.replace(/\n\n/g, '<br><br>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

// ==================
// VOICE INPUT
// ==================
function startVoice() {
    if (IS_GUEST) { showSignupPopup(); return; }
    const micBtn = document.getElementById('mic-btn');
    window.speechSynthesis.cancel();
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Voice input not supported! Please use Google Chrome.');
        return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    const selectedLang = document.getElementById('lang-select').value;
    recognition.lang = selectedLang;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;
    try {
        recognition.start();
        micBtn.classList.add('recording');
        micBtn.innerText = '🔴';
    } catch(e) { console.error(e); }
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('user-input').value = transcript;
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
        sendMessage();
    };
    recognition.onerror = function() {
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
    };
    recognition.onend = function() {
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
    };
}

// ==================
// VOICE OUTPUT
// ==================
function toggleVoice() {
    if (IS_GUEST) { showSignupPopup(); return; }
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voice-toggle-btn');
    if (voiceEnabled) {
        btn.innerText = '🔊';
        btn.style.background = 'rgba(0,120,255,0.3)';
        btn.style.borderColor = '#0078ff';
    } else {
        window.speechSynthesis.cancel();
        btn.innerText = '🔇';
        btn.style.background = '';
        btn.style.borderColor = '';
    }
}

function speakText(text) {
    const selectedLang = document.getElementById('lang-select').value;
    let cleanText = text
        .replace(/#{1,6}\s/g, '').replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1').replace(/`(.*?)`/g, '$1')
        .replace(/\d+\.\s/g, '').replace(/[-•]\s/g, '')
        .replace(/[🏋💪🔥🎯🥗📸🎤✅❌👋⚡]/g, '')
        .replace(/\n+/g, '. ').replace(/\s+/g, ' ').trim().substring(0, 300);
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(cleanText);
    speech.lang = selectedLang;
    speech.rate = 1.0;
    window.speechSynthesis.speak(speech);
}

// ==================
// IMAGE/CAMERA
// ==================
function handleImage(event) {
    if (IS_GUEST) { showSignupPopup(); return; }
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        selectedImage = e.target.result;
        document.getElementById('image-preview').src = selectedImage;
        document.getElementById('image-preview-container').style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    selectedImage = null;
    const container = document.getElementById('image-preview-container');
    if (container) container.style.display = 'none';
    const input = document.getElementById('camera-input');
    if (input) input.value = '';
}

// ==================
// PDF DOWNLOAD
// ==================
async function downloadPDF() {
    if (IS_GUEST) { showSignupPopup(); return; }
    const chatBox = document.getElementById('chat-box');
    const allBotMessages = chatBox.querySelectorAll('.bot-message .message-content');
    if (allBotMessages.length === 0) {
        alert('Ask FitBot for a workout plan first! 💪');
        return;
    }
    let fullChatText = '';
    allBotMessages.forEach(msg => { fullChatText += msg.innerText + '\n\n'; });
    const exercises = parseExercises(fullChatText);
    const btn = document.querySelector('.pdf-btn');
    const originalText = btn.textContent;
    btn.textContent = '⏳ Generating PDF...';
    btn.disabled = true;
    try {
        const response = await fetch('/generate-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workout_plan: exercises, plan_text: fullChatText.substring(0, 3000), plan_type: 'Workout Plan' })
        });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'fitbot_workout_plan.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            btn.textContent = '✅ Downloaded!';
            setTimeout(() => { btn.textContent = originalText; btn.disabled = false; }, 2000);
        }
    } catch (e) {
        btn.textContent = originalText;
        btn.disabled = false;
        alert('Could not generate PDF. Please try again!');
    }
}

function parseExercises(text) {
    const exercises = [];
    const lines = text.split('\n');
    lines.forEach(line => {
        line = line.trim();
        if (!line) return;
        const patterns = [
            /[•\-\*]\s*([A-Za-z\s]+?)[—\-:]\s*(\d+)\s*(?:sets?|x)\s*[x×]\s*(\d+[-\d]*)/i,
            /([A-Za-z][A-Za-z\s]{2,30}?)\s*[—\-]\s*(\d+)\s*[x×]\s*(\d+[-\d]*)/i,
        ];
        for (const pattern of patterns) {
            const match = line.match(pattern);
            if (match) {
                const name = match[1].replace(/[•\-\*\d\.]/g, '').trim();
                if (name.length > 2 && name.length < 50) {
                    exercises.push({ name, sets: match[2] || '3', reps: match[3] || '10-12', rest: '60s' });
                }
                break;
            }
        }
    });
    return exercises.slice(0, 20);
}

// ==================
// LOAD USER STATS
// ==================
async function loadUserStats() {
    if (IS_GUEST) return;
    try {
        const response = await fetch('/api/user-stats');
        const data = await response.json();
        const streakEl = document.getElementById('streak-count');
        const dayEl = document.getElementById('day-number');
        const workoutsEl = document.getElementById('total-workouts');
        const streakBar = document.getElementById('streak-bar');
        if (streakEl) streakEl.textContent = data.streak || 0;
        if (dayEl) dayEl.textContent = data.day_number || 1;
        if (workoutsEl) workoutsEl.textContent = data.total_workouts || 0;
        if (data.streak > 0 && streakBar) streakBar.classList.add('streak-on');
    } catch (e) { console.log('Stats error:', e); }
}

// ==================
// ENTER KEY
// ==================
function handleKey(event) {
    if (event.key === 'Enter') sendMessage();
}

// ==================
// INIT
// ==================
window.addEventListener('load', () => {
    loadUserStats();
    updateGuestCounter();

    // Pre-filled message from exercise page
    const msg = sessionStorage.getItem('fitbot_message');
    if (msg) {
        sessionStorage.removeItem('fitbot_message');
        const input = document.getElementById('user-input');
        if (input) { input.value = msg; setTimeout(() => sendMessage(), 800); }
    }

        // Fetch exercise with GIF
fetch('https://wger.de/api/v2/exercise/?format=json&language=2&category=10')
    .then(r => r.json())
    .then(data => console.log(data))
    
});