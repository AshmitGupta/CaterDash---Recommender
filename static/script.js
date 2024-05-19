const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

const SYSTEM_MESSAGE = "Hi! Welcome to CaterDash! Please let me know the total budget of the event, number of people attending, and your cuisine choice";

document.addEventListener('DOMContentLoaded', (event) => {
    // Clear chat history and initialize with system message
    chatMessages.innerHTML = '';
    appendMessage('assistant', SYSTEM_MESSAGE);
});

sendButton.addEventListener('click', async () => {
    const userMessage = messageInput.value.trim();
    if (userMessage) {
        appendMessage('user', userMessage);
        messageInput.value = '';

        // Read all messages from the chat box
        const messages = Array.from(chatMessages.children).map(msgDiv => {
            const role = msgDiv.classList.contains('user') ? 'user' : 'assistant';
            const content = msgDiv.textContent.trim();
            return { role, content };
        }).filter(msg => msg.content !== '');

        messages.unshift({ role: 'system', content: "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous." });
        messages.unshift({ role: 'system', content: "Don't answer anything that is not related to catering or CaterDash. For anything that you don't have the info for, direct them to www.caterdash.ca" });
        console.log("HERE" + JSON.stringify({ messages }));
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ messages }),
        });

        const result = await response.json();
        const assistantMessage = result.response;

        appendMessage('assistant', assistantMessage);
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
