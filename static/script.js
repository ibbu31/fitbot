let selectedImage = null;
let voiceEnabled = false;

// ==================
// SEND MESSAGE
// ==================
function sendMessage() {
    const input = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const message = input.value.trim();

    if (!message && !selectedImage) return;

    if (message) {
        chatBox.innerHTML += `
            <div class="message user-message">
                <div class="message-content">${message}</div>
            </div>`;
    }

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

    const selectedLang = document.getElementById('lang-select').value;

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message || "I am sending you an image",
            image: selectedImage,
            language: selectedLang
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

        if (voiceEnabled) speakText(data.reply);
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
    } catch(e) {
        console.error("Recognition error:", e);
    }

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('user-input').value = transcript;
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
        sendMessage();
    };

    recognition.onerror = function(event) {
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
        if (event.error === 'not-allowed') {
            alert('Microphone access denied! Please allow microphone in Chrome settings.');
        }
    };

    recognition.onend = function() {
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
    };
}

// ==================
// VOICE OUTPUT — only when user turns ON
// ==================
function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voice-toggle-btn');
    if (voiceEnabled) {
        btn.innerText = '🔊';
        btn.title = 'Voice ON — click to turn off';
        btn.style.background = 'rgba(0,120,255,0.3)';
        btn.style.borderColor = '#0078ff';
    } else {
        window.speechSynthesis.cancel();
        btn.innerText = '🔇';
        btn.title = 'Voice OFF — click to turn on';
        btn.style.background = '';
        btn.style.borderColor = '';
    }
}

function speakText(text) {
    const selectedLang = document.getElementById('lang-select').value;
    let cleanText = text
        .replace(/#{1,6}\s/g, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/`(.*?)`/g, '$1')
        .replace(/\d+\.\s/g, '')
        .replace(/[-•]\s/g, '')
        .replace(/[🏋💪🔥🎯🥗📸🎤✅❌👋⚡💎🏃]/g, '')
        .replace(/\n+/g, '. ')
        .replace(/\s+/g, ' ')
        .trim()
        .substring(0, 300);

    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(cleanText);
    speech.lang = selectedLang;
    speech.rate = 1.0;
    speech.pitch = 1;
    window.speechSynthesis.speak(speech);
}

// ==================
// IMAGE/CAMERA
// ==================
function handleImage(event) {
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
    const chatBox = document.getElementById('chat-box');
    const messages = chatBox.querySelectorAll('.bot-message .message-content');

    if (messages.length === 0) {
        alert('No workout plan to download yet! Ask FitBot for a workout first. 💪');
        return;
    }

    const lastMessage = messages[messages.length - 1].innerText;
    const lines = lastMessage.split('\n').filter(l => l.trim());
    const exercises = [];

    lines.forEach(line => {
        if (line.includes('sets') || line.includes('reps') || line.match(/\d+x\d+/)) {
            exercises.push({
                name: line.split('—')[0].replace(/[•\-*✅💪🏋️]/g, '').trim(),
                sets: '3',
                reps: '10-12',
                rest: '60s'
            });
        }
    });

    const response = await fetch('/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workout_plan: exercises.length > 0 ? exercises : [
                { name: 'See your FitBot chat for full plan', sets: '--', reps: '--', rest: '--' }
            ],
            plan_type: 'Workout Plan'
        })
    });

    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fitbot_workout_plan.pdf';
        a.click();
    } else {
        alert('Could not generate PDF. Please try again!');
    }
}

// ==================
// ENTER KEY
// ==================
function handleKey(event) {
    if (event.key === 'Enter') sendMessage();
}

// Check for pre-filled message from exercise page
window.addEventListener('load', () => {
    const msg = sessionStorage.getItem('fitbot_message');
    if (msg) {
        sessionStorage.removeItem('fitbot_message');
        const input = document.getElementById('user-input');
        if (input) {
            input.value = msg;
            setTimeout(() => sendMessage(), 500);
        }
    }
});