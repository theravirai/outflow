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

        try {
            // Check for CSRF token globally
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfInput = document.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfMeta ? csrfMeta.content : (csrfInput ? csrfInput.value : '');

            const response = await fetch('/api/assistant', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ text })
            });
            
            const data = await response.json();
            removeTyping();
            
            if (data.type === 'error') {
                appendMessage(data.message, 'assistant');
            } else if (data.type === 'chat') {
                appendMessage(data.message, 'assistant');
            } else if (data.type === 'navigation') {
                appendMessage(data.message, 'assistant');
                setTimeout(() => {
                    window.location.href = data.data.url;
                }, 1000);
            } else if (data.type === 'add_expense') {
                appendMessage(data.message, 'assistant');
                
                // Show confirmation card
                const wrapper = document.createElement('div');
                wrapper.className = 'chat-message assistant';
                
                const card = document.createElement('div');
                card.className = 'message-bubble confirmation-card';
                card.innerHTML = `
                    <strong>New Expense</strong><br>
                    Amount: €${parseFloat(data.data.amount).toFixed(2)}<br>
                    Category: ${data.data.category}<br>
                    Date: ${data.data.date}<br>
                    Description: ${data.data.description}<br>
                    <div style="margin-top: 12px; display: flex; gap: 8px;">
                        <button class="btn btn-primary btn-sm confirm-expense-btn">Confirm & Save</button>
                    </div>
                `;
                
                wrapper.appendChild(card);
                messagesContainer.appendChild(wrapper);
                scrollToBottom();
                
                // Add event listener to confirm button
                card.querySelector('.confirm-expense-btn').addEventListener('click', async (e) => {
                    e.target.disabled = true;
                    e.target.textContent = "Saving...";
                    
                    const formData = new FormData();
                    formData.append('amount', data.data.amount);
                    formData.append('category', data.data.category);
                    formData.append('date', data.data.date);
                    formData.append('description', data.data.description);
                    
                    try {
                        const saveResponse = await fetch('/expenses/add', {
                            method: 'POST',
                            headers: { 'X-CSRF-Token': csrfToken },
                            body: formData
                        });
                        
                        if (saveResponse.ok || saveResponse.redirected) {
                            e.target.textContent = "Saved!";
                            appendMessage("I've saved that expense for you.", 'assistant');
                        } else {
                            e.target.textContent = "Failed";
                            appendMessage("There was an error saving the expense.", 'assistant');
                        }
                    } catch (err) {
                        e.target.textContent = "Error";
                        appendMessage("Network error while saving.", 'assistant');
                    }
                });
            }
            
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
                    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                    const csrfInput = document.querySelector('input[name="csrf_token"]');
                    const csrfToken = csrfMeta ? csrfMeta.content : (csrfInput ? csrfInput.value : '');

                    try {
                        const response = await fetch('/api/assistant/transcribe', {
                            method: 'POST',
                            headers: { 'X-CSRF-Token': csrfToken },
                            body: formData
                        });
                        const data = await response.json();
                        
                        if (data.success && data.text) {
                            chatInput.value = data.text;
                            chatInput.dispatchEvent(new Event('input')); // Re-enable send button
                        } else {
                            throw new Error(data.error || "Transcription failed");
                        }
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
