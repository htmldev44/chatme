const socket = io(); // Connect to the server

// Function to send a new message
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value;

    if (message) {
        socket.emit('message', { message: message }); // Emit the message to the server
        messageInput.value = ''; // Clear the input box
    }
}

// Function to ban a user (admin only)
function banUser() {
    const username = document.getElementById('banUsername').value;

    if (username) {
        socket.emit('ban_user', { username: username }); // Emit a ban request
        document.getElementById('banUsername').value = ''; // Clear the input box
    }
}

// Function to unban a user (admin only)
function unbanUser() {
    const username = document.getElementById('banUsername').value;

    if (username) {
        socket.emit('unban_user', { username: username }); // Emit an unban request
        document.getElementById('banUsername').value = ''; // Clear the input box
    }
}

// Function to pin a message (admin only)
function pinMessage() {
    const message = document.getElementById('messageInput').value;

    if (message) {
        socket.emit('pin_message', { message: message }); // Emit a pin message request
        document.getElementById('messageInput').value = ''; // Clear the input box
    }
}

// Function to promote a user to admin (admin only)
function promoteToAdmin() {
    const username = document.getElementById('promoteUsername').value;

    if (username) {
        socket.emit('promote_user', { username: username }); // Emit a promotion request
        document.getElementById('promoteUsername').value = ''; // Clear the input box
    }
}

// Function to shut down the server (admin only)
function shutdownServer() {
    fetch('/shutdown', { method: 'POST' })
        .then(response => response.text())
        .then(message => alert(message))
        .catch(err => console.error("Error shutting down the server:", err));
}

// Listen for new messages from the server
socket.on('new_message', (msg) => {
    const messagesDiv = document.getElementById('messages');
    const messageElement = document.createElement('p');
    messageElement.textContent = msg;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to the bottom
});

// Listen for pinned messages
socket.on('pin_message', (msg) => {
    const pinnedDiv = document.getElementById('pinnedMessage');
    pinnedDiv.style.display = 'block';
    pinnedDiv.textContent = "Pinned: " + msg;
});

// Listen for system messages (e.g., ban/unban notifications or promotions)
socket.on('system_message', (msg) => {
    const messagesDiv = document.getElementById('messages');
    const systemMessageElement = document.createElement('p');
    systemMessageElement.style.fontWeight = 'bold'; // Highlight system messages
    systemMessageElement.textContent = "System: " + msg;
    messagesDiv.appendChild(systemMessageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});

// Prevent accidental form submission (if any forms are present)
document.addEventListener('submit', (e) => e.preventDefault());