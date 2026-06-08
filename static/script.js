function sendMessage() {
    const input = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const message = input.value.trim();

    // Don't send empty messages
    if (!message) return;

    // Show user message
    chatBox.innerHTML += `
        <div class="message user-message">${message}</div>
    `;

    // Clear input
    input.value = '';

    // Show typing indicator
    chatBox.innerHTML += `
        <div class="typing" id="typing">FitBot is thinking... 💭</div>
    `;

    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;

    // Send to Flask backend
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        document.getElementById('typing').remove();

        // Show bot reply
        chatBox.innerHTML += `
            <div class="message bot-message">${data.reply}</div>
        `;

        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        // Remove typing indicator
        document.getElementById('typing').remove();

        // Show error message
        chatBox.innerHTML += `
            <div class="message bot-message">
                ❌ Something went wrong. Please try again!
            </div>
        `;
    });
}

// Send message when Enter key is pressed
function handleKey(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}