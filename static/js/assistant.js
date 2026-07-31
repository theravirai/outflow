document.addEventListener('DOMContentLoaded', () => {
    const fab = document.getElementById('ai-assistant-fab');
    const panel = document.getElementById('ai-chat-panel');
    const closeBtn = document.getElementById('ai-close-btn');
    const chatForm = document.getElementById('ai-chat-form');
    const chatInput = document.getElementById('ai-chat-input');
    const sendBtn = document.getElementById('ai-send-btn');
    const voiceBtn = document.getElementById('ai-voice-btn');
    const messagesContainer = document.getElementById('chat-messages');

    if (!fab || !panel) return; // Not authenticated

    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];

    // --- Panel Toggle Logic ---
    const togglePanel = () => {
        const isOpen = panel.classList.contains('open');
        if (isOpen) {
            panel.classList.remove('open');
            panel.setAttribute('aria-hidden', 'true');
        } else {
            panel.classList.add('open');
            panel.setAttribute('aria-hidden', 'false');
            fab.classList.remove('pulse'); // Remove pulse permanently once opened
            localStorage.setItem('outflow_ai_visited', 'true');
            chatInput.focus();
            scrollToBottom();
        }
    };

    fab.addEventListener('click', togglePanel);
    closeBtn.addEventListener('click', togglePanel);

    // Close on Escape or click outside
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && panel.classList.contains('open')) {
            togglePanel();
        }
    });

    document.addEventListener('click', (e) => {
        if (panel.classList.contains('open') && 
            !panel.contains(e.target) && 
            !fab.contains(e.target)) {
            togglePanel();
        }
    });

    // Pulse on first visit
    if (!localStorage.getItem('outflow_ai_visited')) {
        fab.classList.add('pulse');
    }

    // --- Chat History & State ---
    const loadHistory = () => {
        const history = sessionStorage.getItem('outflow_ai_history');
        if (history) {
            messagesContainer.innerHTML = history;
            if (window.lucide) window.lucide.createIcons({ root: messagesContainer });
            scrollToBottom();
        } else {
            renderSuggestions();
        }
    };

    const saveHistory = () => {
        // Don't save if there's a typing indicator
        if (!messagesContainer.querySelector('.typing-indicator')) {
            sessionStorage.setItem('outflow_ai_history', messagesContainer.innerHTML);
        }
    };

    const scrollToBottom = () => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    // --- UI Rendering ---
    const formatTime = () => {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const renderSuggestions = () => {
        const suggestions = [
            "Add €25 spent on groceries",
            "I paid rent today",
            "How much did I spend this month?",
            "What is my largest expense?",
            "Compare this month with last month"
        ];
        
        const container = document.createElement('div');
        container.className = 'suggestions-container';
        
        suggestions.forEach(text => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-chip';
            btn.textContent = text;
            btn.addEventListener('click', () => {
                chatInput.value = text;
                chatInput.focus();
                sendBtn.disabled = false;
            });
            container.appendChild(btn);
        });
        
        messagesContainer.appendChild(container);
    };

    const clearSuggestions = () => {
        const suggestions = messagesContainer.querySelector('.suggestions-container');
        if (suggestions) suggestions.remove();
    };

    const appendMessage = (text, sender = 'user') => {
        clearSuggestions();
        
        const wrapper = document.createElement('div');
        wrapper.className = `chat-message ${sender}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // Very basic markdown handling for bolding
        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Handle newlines
        formattedText = formattedText.replace(/\n/g, '<br>');
        
        bubble.innerHTML = formattedText;
        
        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = formatTime();
        
        wrapper.appendChild(bubble);
        wrapper.appendChild(time);
        
        messagesContainer.appendChild(wrapper);
        scrollToBottom();
        saveHistory();
    };

    const showTyping = () => {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-message assistant typing-msg';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble typing-indicator';
        bubble.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        wrapper.appendChild(bubble);
        messagesContainer.appendChild(wrapper);
        scrollToBottom();
    };

    const removeTyping = () => {
        const typingMsg = messagesContainer.querySelector('.typing-msg');
        if (typingMsg) typingMsg.remove();
    };

    // --- Interaction Logic ---
    chatInput.addEventListener('input', () => {
        sendBtn.disabled = chatInput.value.trim().length === 0;
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        sendBtn.disabled = true;
        chatInput.disabled = true;
        
        appendMessage(text, 'user');
        showTyping();

        // Step 5 API Placeholder logic
        try {
            // Check for CSRF token
            const csrfInput = document.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfInput ? csrfInput.value : '';

            // TODO: In Step 3-5, this will hit /api/assistant
            // Mock delay for now
            await new Promise(resolve => setTimeout(resolve, 1500));
            removeTyping();
            
            appendMessage("I am currently in UI construction mode. My brain (the backend AI logic) will be connected in Step 3!", 'assistant');
            
        } catch (error) {
            removeTyping();
            appendMessage("I'm unable to reach the AI service right now. Please try again in a moment.", 'assistant');
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
        }
    });

    // --- Voice Input Logic ---
    voiceBtn.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    chatInput.placeholder = "Transcribing...";
                    chatInput.disabled = true;
                    voiceBtn.classList.remove('recording');
                    
                    const formData = new FormData();
                    formData.append("audio", audioBlob, "assistant.webm");

                    // CSRF Token
                    const csrfInput = document.querySelector('input[name="csrf_token"]');
                    const csrfToken = csrfInput ? csrfInput.value : '';

                    try {
                        // TODO: Implement /api/assistant/transcribe in backend
                        chatInput.value = "Voice transcription endpoint pending step 5...";
                        sendBtn.disabled = false;
                    } catch (error) {
                        console.error("Transcription failed", error);
                        chatInput.placeholder = "Ask a question...";
                    } finally {
                        chatInput.disabled = false;
                        chatInput.placeholder = "Ask a question or add an expense...";
                        stream.getTracks().forEach(track => track.stop());
                    }
                });

                mediaRecorder.start();
                isRecording = true;
                voiceBtn.classList.add('recording');
                chatInput.placeholder = "Listening...";
                
            } catch (err) {
                console.error("Microphone access denied", err);
                alert("Microphone access is required for voice input.");
            }
        } else {
            mediaRecorder.stop();
            isRecording = false;
        }
    });

    // Initialize
    loadHistory();
});
