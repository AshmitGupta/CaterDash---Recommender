const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

sendButton.addEventListener('click', async () => {
    const userMessage = messageInput.value.trim();
    if (userMessage) {
        appendMessage('user', userMessage);
        messageInput.value = '';

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userMessage }),
        });

        const result = await response.json();
        appendMessage('assistant', result.response);
    }
});

function appendMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = `chat-bubble ${role}`;
    bubbleDiv.textContent = text;
    messageDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}