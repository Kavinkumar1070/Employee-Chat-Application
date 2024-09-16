// Predefined questions for the AI
const questions = [
    "What can you help me with?",
    "How does AI work?",
    "What are your abilities?",
    "Tell me a joke!",
    "What is the weather today?"
];

// Bot responses for specific questions
const responses = {
    "how does ai work?": "AI uses algorithms and data to simulate human-like decision-making and learning.",
    "what can you help me with?": "I can assist you with answering questions, providing information, and guiding you through processes.",
    "what are your abilities?": "I can process language, analyze data, and assist with a variety of tasks like answering questions or helping with decisions.",
    "tell me a joke!": "Why don't robots take vacations? Because they never need to recharge!",
    "what is the weather today?": "I currently can't check real-time weather, but you can use an online service to find out!"
};

// Initial bot response for greetings
const initialResponses = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! What can I do for you?",
    "hey": "Hey! How can I help you today?"
};

// Track the number of interactions
let interactionCount = 0;
const maxInteractions = 5;

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const lists = document.getElementById("lists");

function displayQuestions() {
    setTimeout(() => {
        questions.forEach(question => {
            const questionCard = document.createElement("div");
            questionCard.classList.add("card");
            questionCard.innerHTML = question;
            lists.appendChild(questionCard);
        });
    }, 1000);
}

function sendMessage() {
    const message = userInput.value.trim().toLowerCase();
    if (message === "") return;

    // Hide the questions list if present

    addMessageToChat(message, 'user');

    let responseMessage = '';

    // Check if input matches a specific question for a relevant response
    if (responses[message]) {
        responseMessage = responses[message];
    } 
    // Check for initial greetings
    else if (initialResponses[message]) {
        responseMessage = initialResponses[message];
    } 
    // Generic responses or prompt login after a few interactions
    else {
        interactionCount++;
        if (interactionCount < maxInteractions) {
            responseMessage = "That's interesting! Do you have any other questions?";
        } else {
            responseMessage = "To continue this conversation, please log in.";

            // Disable input after prompting login
            userInput.disabled = true;
            sendButton.disabled = true;
        }
    }

    addMessageToChat(responseMessage, 'bot');
    userInput.value = "";
}

function addMessageToChat(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.classList.add('regular-message'); // Regular message styling
    messageElement.innerHTML = message; // Use innerHTML to render HTML content

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

// Display the predefined questions when the page loads
window.onload = displayQuestions;
