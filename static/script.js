let selectedImage = null;
let voiceEnabled = false;
// ==================
// LOAD USER STATS (streak, day, workouts)
// ==================
async function loadUserStats() {
    try {
        const response = await fetch('/api/user-stats');
        const data = await response.json();

        // Update streak
        const streakEl = document.getElementById('streak-count');
        const dayEl = document.getElementById('day-number');
        const workoutsEl = document.getElementById('total-workouts');
        const streakBar = document.getElementById('streak-bar');

        if (streakEl) streakEl.textContent = data.streak || 0;
        if (dayEl) dayEl.textContent = data.day_number || 1;
        if (workoutsEl) workoutsEl.textContent = data.total_workouts || 0;

        // Animate fire if streak > 0
        if (data.streak > 0 && streakBar) {
            streakBar.classList.add('streak-on');
        }

        // Show onboarding banner for new users (day 1, no workouts)
        const banner = document.getElementById('onboarding-banner');
        if (banner && data.day_number <= 3 && data.total_workouts === 0) {
            banner.style.display = 'flex';
        }

    } catch (e) {
        console.log('Stats load error:', e);
    }
}

// ==================
// QUICK START — fast first workout
// ==================
function quickStart(goal) {
    document.getElementById('onboarding-banner').style.display = 'none';

    const messages = {
        weight_loss: "I want to lose weight. I'm a beginner with no equipment. Give me a quick 7-day workout plan to start TODAY!",
        muscle_gain: "I want to build muscle. I'm a beginner. Give me a workout plan to start TODAY!",
        general_fitness: "I want to get fit and healthy. Give me a simple workout plan to start TODAY!"
    };

    document.getElementById('user-input').value = messages[goal] || messages.general_fitness;
    sendMessage();
}

// Load stats when page opens
window.addEventListener('load', () => {
    loadUserStats();

    // Check for pre-filled message from exercise page
    const msg = sessionStorage.getItem('fitbot_message');
    if (msg) {
        sessionStorage.removeItem('fitbot_message');
        const input = document.getElementById('user-input');
        if (input) {
            input.value = msg;
            setTimeout(() => sendMessage(), 800);
        }
    }
});

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
    const allBotMessages = chatBox.querySelectorAll('.bot-message .message-content');

    if (allBotMessages.length === 0) {
        alert('No workout plan yet! Ask FitBot for a workout plan first. 💪');
        return;
    }

    // Collect ALL bot messages into one text
    let fullChatText = '';
    allBotMessages.forEach(msg => {
        fullChatText += msg.innerText + '\n\n';
    });

    // Parse exercises from text
    const exercises = parseExercises(fullChatText);

    // Also get the full plan text for the PDF
    const planText = fullChatText.substring(0, 3000);

    const btn = document.querySelector('.pdf-btn');
    const originalText = btn.textContent;
    btn.textContent = '⏳ Generating PDF...';
    btn.disabled = true;

    try {
        const response = await fetch('/generate-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                workout_plan: exercises,
                plan_text: planText,
                plan_type: 'Workout Plan'
            })
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
            window.URL.revokeObjectURL(url);
            btn.textContent = '✅ Downloaded!';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.disabled = false;
            }, 2000);
        } else {
            throw new Error('PDF generation failed');
        }
    } catch (error) {
        alert('Could not generate PDF. Please try again!');
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Parse exercises from chat text
function parseExercises(text) {
    const exercises = [];
    const lines = text.split('\n');

    lines.forEach(line => {
        line = line.trim();
        if (!line) return;

        // Skip header lines
        if (line.startsWith('👋') || line.startsWith('Welcome')) return;

        // Match patterns like:
        // • Push Up — 3 sets x 12 reps (60s rest)
        // Push Up: 3 sets, 12 reps
        // 1. Push Up - 3x12
        // • Push Up — 3 x 12

        const exercisePatterns = [
            // Pattern: • Exercise — 3 sets x 12 reps (60s)
            /[•\-\*]\s*([A-Za-z\s]+?)[—\-:]\s*(\d+)\s*(?:sets?|x)\s*[x×]\s*(\d+[-\d]*)\s*(?:reps?)?(?:\s*[\(\[]([^\)\]]+)[\)\]])?/i,
            // Pattern: Exercise — 3 x 12 reps
            /([A-Za-z][A-Za-z\s]{2,30}?)\s*[—\-]\s*(\d+)\s*[x×]\s*(\d+[-\d]*)\s*(?:reps?)?/i,
            // Pattern: Exercise: sets x reps
            /([A-Za-z][A-Za-z\s]{2,30}?):\s*(\d+)\s*(?:sets?)?\s*[x×,]\s*(\d+[-\d]*)\s*(?:reps?)?/i,
        ];

        for (const pattern of exercisePatterns) {
            const match = line.match(pattern);
            if (match) {
                const name = match[1].replace(/[•\-\*\d\.]/g, '').trim();
                if (name.length > 2 && name.length < 50) {
                    exercises.push({
                        name: name,
                        sets: match[2] || '3',
                        reps: match[3] || '10-12',
                        rest: match[4] || '60s'
                    });
                }
                break;
            }
        }
    });

    // If no exercises parsed, create entries from bullet points
    if (exercises.length === 0) {
        lines.forEach(line => {
            line = line.trim();
            if ((line.startsWith('•') || line.startsWith('-') || line.match(/^\d+\./)) && line.length > 5 && line.length < 100) {
                const name = line.replace(/^[•\-\*\d\.]\s*/, '').split('—')[0].split(':')[0].trim();
                if (name.length > 2) {
                    exercises.push({ name: name, sets: '3', reps: '10-12', rest: '60s' });
                }
            }
        });
    }

    return exercises.slice(0, 20); // Max 20 exercises
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
        // Fetch exercise with GIF
fetch('https://wger.de/api/v2/exercise/?format=json&language=2&category=10')
    .then(r => r.json())
    .then(data => console.log(data))
    }
});