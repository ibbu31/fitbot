let selectedImage = null;
let voiceEnabled = false;
let guestMessageCount = parseInt(localStorage.getItem('mentro.fit_guest_msgs') || '0');

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
        localStorage.setItem('mentro.fit_guest_msgs', guestMessageCount);
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
chatBox.innerHTML += `<div class="typing" id="typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;

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
            <div class="bot-avatar">M</div>
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
                <div class="bot-avatar">M</div>
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
        btn.style.background = 'rgba(255,90,31,0.25)';
        btn.style.borderColor = '#FF5A1F';
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

    // NOTE: the illustrated avatar element (#avatar-face) that this used
    // to pulse while speaking was removed along with the rest of the
    // avatar feature, so the speaking-state toggle has been removed too.

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
        alert('Ask Mentro for a workout plan first!');
        return;
    }
    let fullChatText = '';
    allBotMessages.forEach(msg => { fullChatText += msg.innerText + '\n\n'; });
    const exercises = parseExercises(fullChatText);
 
    const card = document.getElementById('pdf-card');
    const originalHTML = card.innerHTML;
 
    // Step 1 — "generating" state, matches a document-creation flow
    card.innerHTML = `
        <button class="pdf-btn" disabled>
            <span class="pdf-spinner"></span>
            Creating your plan...
        </button>`;
 
    try {
        const response = await fetch('/generate-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workout_plan: exercises, plan_text: fullChatText.substring(0, 3000), plan_type: 'Workout Plan' })
        });
 
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const sizeKb = Math.max(1, Math.round(blob.size / 1024));
            const filename = 'mentro_workout_plan.pdf';
 
            // Step 2 — "file ready" card, like a generated-document result
            card.innerHTML = `
                <div class="pdf-file-ready">
                    <div class="pdf-file-icon">PDF</div>
                    <div class="pdf-file-info">
                        <span class="pdf-file-name">${filename}</span>
                        <span class="pdf-file-meta">${sizeKb} KB</span>
                    </div>
                    <button class="pdf-file-download-btn" id="pdf-save-btn">Save</button>
                </div>`;
 
            document.getElementById('pdf-save-btn').onclick = () => {
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            };
 
            // Auto-trigger the first download immediately too
            document.getElementById('pdf-save-btn').click();
 
        } else {
            throw new Error('PDF generation failed');
        }
    } catch (e) {
        card.innerHTML = originalHTML;
        alert('Could not generate PDF. Please try again!');
    }
}
// ==================
// LOAD USER STATS
// ==================
async function loadUserStats() {
        if (IS_GUEST) return;
        try {
            const response = await fetch('/api/user-stats');
            const data = await response.json();
 
            const streak = data.streak || 0;
            const weekly = data.weekly_workouts || 0;
            const weeklyGoal = data.weekly_goal || 4;
            const total = data.total_workouts || 0;
 
            const streakEl = document.getElementById('streak-count');
            const weeklyEl = document.getElementById('weekly-count');
            const workoutsEl = document.getElementById('total-workouts');
            if (streakEl) streakEl.textContent = streak;
            if (weeklyEl) weeklyEl.textContent = weekly;
            if (workoutsEl) workoutsEl.textContent = total;
 
            // Ring circumference = 2 * PI * r(42) = ~264. Cap each ring's fill at 100%.
            const CIRCUMFERENCE = 264;
            setRingProgress('ring-streak', Math.min(streak / 7, 1), CIRCUMFERENCE);
            setRingProgress('ring-weekly', Math.min(weekly / weeklyGoal, 1), CIRCUMFERENCE);
            setRingProgress('ring-total', Math.min(total / 20, 1), CIRCUMFERENCE);
        } catch (e) { console.log('Stats error:', e); }
    }
 
    function setRingProgress(elementId, fraction, circumference) {
        const ring = document.getElementById(elementId);
        if (!ring) return;
        const offset = circumference - (fraction * circumference);
        // Small delay so the fill animates in after page load, not instantly
        setTimeout(() => { ring.style.strokeDashoffset = offset; }, 200);
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

    // NOTE: the leftover wger.de exercise-GIF fetch that used to run on
    // every page load (and only logged its result to the console without
    // using it) has been removed — it was a leftover from evaluating
    // exercise-data APIs and just added an unnecessary network request
    // on every load, which mattered more on mobile.
});
const quizAnswers = { goal: '', level: '', equipment: '', injuries: '' };
let currentQuizStep = 1;
const totalQuizSteps = 4;
 
function selectQuizOption(btn, field) {
    quizAnswers[field] = btn.dataset.value;
 
    // Visual selected state
    btn.parentElement.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
    btn.classList.add('selected');
 
    // Auto-advance after a short pause, or submit if last step
    setTimeout(() => {
        if (currentQuizStep < totalQuizSteps) {
            goToQuizStep(currentQuizStep + 1);
        } else {
            submitOnboarding();
        }
    }, 350);
}
 
function goToQuizStep(step) {
    document.querySelectorAll('.quiz-step').forEach(s => s.classList.remove('active'));
    document.querySelector(`.quiz-step[data-step="${step}"]`).classList.add('active');
 
    document.querySelectorAll('.quiz-dot').forEach(d => {
        const dotStep = parseInt(d.dataset.step);
        d.classList.remove('active', 'done');
        if (dotStep === step) d.classList.add('active');
        else if (dotStep < step) d.classList.add('done');
    });
 
    currentQuizStep = step;
    document.getElementById('quiz-back-btn').style.display = step > 1 ? 'block' : 'none';
}
 
function quizBack() {
    if (currentQuizStep > 1) goToQuizStep(currentQuizStep - 1);
}
 
function submitOnboarding() {
    fetch('/api/onboarding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(quizAnswers)
    })
    .then(r => r.json())
    .then(() => {
        const overlay = document.getElementById('quiz-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
        }
        // Send an opening message so mentro.fit immediately responds using the new profile
        setTimeout(() => {
            const input = document.getElementById('user-input');
            if (input) {
                input.value = "Based on what I just told you, give me my first workout plan!";
                sendMessage();
            }
        }, 400);
    })
    .catch(e => console.log('Onboarding save error:', e));
}


// ==================
// REFERRAL LINK
// ==================
function copyReferralLink() {
    const linkEl = document.getElementById('referral-link-display');
    if (!linkEl) return;
    const fullLink = 'https://' + linkEl.textContent.trim();
    navigator.clipboard.writeText(fullLink).then(() => {
        const btn = document.querySelector('.referral-copy-btn');
        const original = btn.textContent;
        btn.textContent = 'Copied! ✓';
        setTimeout(() => { btn.textContent = original; }, 1800);
    }).catch(() => {
        alert('Copy this link: ' + fullLink);
    });
}

// ==================
// PREMIUM WAITLIST
// ==================
function joinWaitlist() {
    const btn = document.getElementById('waitlist-btn');
    fetch('/api/join-waitlist', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                btn.textContent = "✅ You're on the list!";
                btn.disabled = true;
            }
        })
        .catch(e => console.log('Waitlist error:', e));
}