let selectedImage = null;
let voiceEnabled = true;

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
            <div class="message user-message">${message}</div>
        `;
    }

    if (selectedImage) {
        chatBox.innerHTML += `
            <div class="message user-message">
                <img src="${selectedImage}" class="user-image"/>
            </div>
        `;
    }

    input.value = '';
    clearImage();

    chatBox.innerHTML += `
        <div class="typing" id="typing">FitBot is thinking... 💭</div>
    `;
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: message || "I am sending you an image",
            image: selectedImage
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('typing').remove();
        chatBox.innerHTML += `
            <div class="message bot-message">${data.reply}</div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;

        // Only speak if voice is enabled
        if (voiceEnabled) {
            speakText(data.reply);
        }
    })
    .catch(error => {
        document.getElementById('typing').remove();
        chatBox.innerHTML += `
            <div class="message bot-message">❌ Something went wrong. Please try again!</div>
        `;
    });
}

// ==================
// VOICE INPUT 🎤
// ==================
function startVoice() {
    const micBtn = document.getElementById('mic-btn');

    // Stop any current speaking before listening
    window.speechSynthesis.cancel();

    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        alert('Please use Google Chrome for voice input!');
        return;
    }

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();
    micBtn.classList.add('recording');
    micBtn.innerText = '🔴';

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
// VOICE OUTPUT 🔊
// ==================
function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voice-toggle-btn');
    if (voiceEnabled) {
        btn.innerText = '🔊';
        btn.title = 'Voice ON';
    } else {
        window.speechSynthesis.cancel();
        btn.innerText = '🔇';
        btn.title = 'Voice OFF';
    }
}

function speakText(text) {
    // Only speak first 200 characters to keep it short
    const shortText = text.replace(/[#*🏋💪🔥🎯]/g, '').substring(0, 200);
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(shortText);
    speech.lang = 'en-US';
    speech.rate = 1.1;
    speech.pitch = 1;
    window.speechSynthesis.speak(speech);
}

// ==================
// IMAGE/CAMERA 📸
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
    document.getElementById('image-preview-container').style.display = 'none';
    document.getElementById('camera-input').value = '';
}

// ==================
// ENTER KEY
// ==================
function handleKey(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}