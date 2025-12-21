document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatBox = document.getElementById('chatBox');
    const closeChat = document.getElementById('closeChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');
    const chatHistorySelect = document.getElementById('chatHistorySelect');
    const newChatBtn = document.getElementById('newChatBtn');
    
    let currentChatId = 'default';
    let chatHistory = {};

    // Load chat history from localStorage
    function loadChatHistory() {
        const savedHistory = localStorage.getItem('chatHistory');
        if (savedHistory) {
            chatHistory = JSON.parse(savedHistory);
            updateChatSelector();
            loadCurrentChat();
        } else {
            chatHistory = {
                default: {
                    name: 'Default Chat',
                    messages: ''
                }
            };
        }
    }
    
    // Save chat history to localStorage
    function saveChatHistory() {
        // Save current messages before storing history
        chatHistory[currentChatId].messages = chatMessages.innerHTML;
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }

    // Update chat selector dropdown
    function updateChatSelector() {
        chatHistorySelect.innerHTML = '';
        Object.keys(chatHistory).forEach(chatId => {
            const option = document.createElement('option');
            option.value = chatId;
            option.textContent = chatHistory[chatId].name;
            if (chatId === currentChatId) {
                option.selected = true;
            }
            chatHistorySelect.appendChild(option);
        });
    }

    // Load the current chat
    function loadCurrentChat() {
        if (chatHistory[currentChatId]) {
            chatMessages.innerHTML = chatHistory[currentChatId].messages;
            // Reattach click handlers for images
            const savedImageMessages = chatMessages.querySelectorAll('.chat-image-message');
            savedImageMessages.forEach(msg => {
                const img = msg.querySelector('img');
                if (img) {
                    msg.addEventListener('click', function() {
                        showModal(img.src, img.getAttribute('data-keyframe'));
                    });
                }
            });
        } else {
            chatMessages.innerHTML = '';
        }
    }

            // Create new chat
    function createNewChat(chatName) {
        if (!chatName) {
            chatName = prompt('Enter a name for the new chat:', 'New Chat');
        }
        if (chatName) {
            // Check if chat name already exists
            const existingChat = Object.values(chatHistory).find(chat => chat.name === chatName);
            if (existingChat) {
                // Add error message to current chat
                const errorMsg = document.createElement('div');
                errorMsg.className = 'message system-message';
                errorMsg.textContent = `Cannot create chat: Name "${chatName}" already exists`;
                errorMsg.style.color = '#721c24';
                errorMsg.style.backgroundColor = '#f8d7da';
                errorMsg.style.border = '1px solid #f5c6cb';
                errorMsg.style.marginBottom = '10px';
                chatMessages.appendChild(errorMsg);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                return;
            }

            // Save current chat before switching
            saveChatState();

            // Create new chat
            const chatId = 'chat_' + Date.now();
            chatHistory[chatId] = {
                name: chatName,
                messages: ''
            };
            currentChatId = chatId;
            
            // Clear and update UI
            chatMessages.innerHTML = '';
            updateChatSelector();
            saveChatHistory();
        }
    }

    // Helper function to save current chat state
    function saveChatState() {
        if (currentChatId && chatHistory[currentChatId]) {
            chatHistory[currentChatId].messages = chatMessages.innerHTML;
        }
    }    // Event listener for chat selection
    chatHistorySelect.addEventListener('change', function(e) {
        // Save current chat state
        saveChatState();
        
        // Switch to new chat
        currentChatId = e.target.value;
        chatMessages.innerHTML = '';
        
        // Load selected chat content
        if (chatHistory[currentChatId] && chatHistory[currentChatId].messages) {
            chatMessages.innerHTML = chatHistory[currentChatId].messages;
            // Reattach click handlers for images
            const savedImageMessages = chatMessages.querySelectorAll('.chat-image-message');
            savedImageMessages.forEach(msg => {
                const img = msg.querySelector('img');
                if (img) {
                    msg.addEventListener('click', function() {
                        showModal(img.src, img.getAttribute('data-keyframe'));
                    });
                }
            });
        }
        
        saveChatHistory();
    });

    // Event listener for new chat button
    newChatBtn.addEventListener('click', createNewChat);

    // Load chat history when page loads
    loadChatHistory();

    // Toggle chat box
    chatButton.addEventListener('click', function() {
        chatBox.classList.toggle('active');
        if (chatBox.classList.contains('active')) {
            messageInput.focus();
        }
    });

    // Close chat box
    closeChat.addEventListener('click', function() {
        chatBox.classList.remove('active');
    });

    // Send message function
    function sendChatMessage() {
        const message = messageInput.value.trim();
        if (message) {
            // Check for commands
            if (message === '\\clear') {
                // Clear current chat messages
                chatMessages.innerHTML = '';
                messageInput.value = '';
                chatHistory[currentChatId].messages = '';
                saveChatHistory();
                return;
            }
            
            if (message === '\\clear_all') {
                // Clear all chat histories
                chatHistory = {
                    default: {
                        name: 'Default Chat',
                        messages: ''
                    }
                };
                currentChatId = 'default';
                chatMessages.innerHTML = '';
                messageInput.value = '';
                saveChatHistory();
                updateChatSelector();
                return;
            }

            if (message.startsWith('\\new ')) {
                // Create new chat with given name
                const chatName = message.substring(5).trim();
                if (chatName) {
                    createNewChat(chatName);
                    messageInput.value = '';
                    return;
                }
            }

            if (message === '\\delete' || message.startsWith('\\delete ')) {
                // Delete current chat or specified chat
                const chatName = message.substring(8).trim();
                if (chatName) {
                    // Find chat by name
                    const chatId = Object.keys(chatHistory).find(
                        id => chatHistory[id].name === chatName
                    );
                    if (chatId && chatId !== 'default') {
                        delete chatHistory[chatId];
                        if (currentChatId === chatId) {
                            currentChatId = 'default';
                            loadCurrentChat();
                        }
                        updateChatSelector();
                        saveChatHistory();
                    } else {
                        // Show error message in chat
                        const errorMsg = document.createElement('div');
                        errorMsg.className = 'message system-message';
                        errorMsg.textContent = `Cannot find or delete chat: ${chatName}`;
                        chatMessages.appendChild(errorMsg);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                } else if (currentChatId !== 'default') {
                    // Delete current chat
                    delete chatHistory[currentChatId];
                    currentChatId = 'default';
                    loadCurrentChat();
                    updateChatSelector();
                    saveChatHistory();
                }
                messageInput.value = '';
                return;
            }

            // Add user message
            const userMessage = document.createElement('div');
            userMessage.className = 'message user-message';
            userMessage.style.marginLeft = 'auto';
            userMessage.style.backgroundColor = '#000000';
            userMessage.style.color = 'white';
            userMessage.textContent = message;
            chatMessages.appendChild(userMessage);

            // Clear input
            messageInput.value = '';

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Save to chat history
            saveChatHistory();
        }
    }

    // Send message on button click
    sendMessage.addEventListener('click', sendChatMessage);

    // Send message on Enter key
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });

    // Add image to chat function
    window.addImageToChat = function(imageUrl, videoId, keyframe) {
        const imageMessage = document.createElement('div');
        imageMessage.className = 'message chat-image-message';
        imageMessage.innerHTML = `
            <img src="${imageUrl}" alt="Selected frame" data-keyframe="${keyframe}">
            <div class="chat-image-info">
                Video ID: ${videoId}<br>
                Keyframe: ${keyframe}
            </div>
        `;
        
        // Add click handler to show video
        imageMessage.addEventListener('click', function() {
            showModal(imageUrl, keyframe);
        });
        
        chatMessages.appendChild(imageMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        chatBox.classList.add('active'); // Show chat box when adding image
        
        // Save to chat history after adding image
        saveChatHistory();
    };



});
