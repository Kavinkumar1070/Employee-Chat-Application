const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const lists = document.getElementById("lists");
let employeeId = null;
let role = null;

const token = localStorage.getItem('token');
console.log(token);

if (token) {
    fetchProfileInfo(token);
} else {
    document.getElementById('welcome-message').innerText = "Welcome!";
    enableInput(); // Enable input if no token is found
}

async function fetchProfileInfo(token) {
    try {
        const response = await fetch('/profile', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch profile info');
        }

        const profile = await response.json();
        employeeId = profile.Employee_ID;
        role = profile.Role;

        // Dynamically populate the list with functions
        setTimeout(() => {(profile.Functions || []).forEach((data) => {
            const listItem = document.createElement("div");
            listItem.classList.add("card");
            listItem.innerHTML = data;
            lists.appendChild(listItem);
        });
        }, 1000);

        document.getElementById('welcome-message').innerText = `Welcome, Your Role is: ${profile.Role} Your Employee ID is: ${employeeId}.`;
        enableInput(); // Enable input after fetching profile info

    } catch (error) {
        document.getElementById('welcome-message').innerText = "Welcome!";
        console.error(error);
        enableInput(); // Enable input even if fetching profile fails
    }
}

function enableInput() {
    userInput.disabled = false;
    sendButton.disabled = false;
}

const websocket = new WebSocket("ws://127.0.0.1:8000/ws/chat");

websocket.onopen = () => {
    console.log("WebSocket connection established.");
};

websocket.onmessage = (event) => {
    const message = event.data;

    // Check if the message starts with <!DOCTYPE html> indicating HTML content
    if (message.startsWith("<!DOCTYPE html>")) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = message;

        const table = tempDiv.querySelector('table');
        const otherContent = tempDiv.innerHTML;

        if (table) {
            chatBox.innerHTML += `<div class="table-wrapper">${table.outerHTML}</div>`;
        } else {
            chatBox.innerHTML += `<div class="message-content">${otherContent}</div>`;
        }
    } else if (message === "Server Error" || message === "Backend Error") {
        window.location.href = "/templates/complete.html";  // Redirect in case of errors
    } else {
        addMessageChat(message, 'bot');
    }
};

function sendMessage() {
    const message = userInput.value;
    if (message.trim() === "") return;
    if (lists) {
        lists.style.display = 'none';
    }
    addMessageToChat(message, 'user');

    const payload = {
        message: message,
        employee_id: employeeId,
        role: role,
        token: token
    };
    console.log('payload', payload);
    websocket.send(JSON.stringify(payload));

    userInput.value = "";
}

function addMessageToChat(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.classList.add('regular-message'); // Regular message styling
    messageElement.innerHTML = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    messageElement.innerHTML = message; // Use innerHTML to render HTML content
             
    const innerMessageElement = document.createElement('div');
    innerMessageElement.classList.add("iconu");
    const parent = document.createElement('div');
    parent.appendChild(innerMessageElement);
    parent.classList.add("parent")
    messageElement.appendChild(parent);
}

function addMessageChat(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.classList.add('message-content'); // Apply specific class for bot messages
    
    messageElement.innerHTML = message;
    const innerMessageElement = document.createElement('div');
    innerMessageElement.classList.add("icon");
    messageElement.appendChild(innerMessageElement);



    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = message;
    const table = tempDiv.querySelector('table');

    if (table) {
        messageElement.classList.add('table-message');
        messageElement.style.width ="100%";
    }

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});
