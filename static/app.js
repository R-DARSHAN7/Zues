const chatHistory = document.getElementById('chat-history');
const micBtn = document.getElementById('mic-btn');
const statusText = document.getElementById('status-text');
const visualizer = document.getElementById('audio-visualizer');
const ttsAudio = document.getElementById('tts-audio');
const statusIndicator = document.querySelector('.status-indicator');
const profileSelect = document.getElementById('profile-select');
const typingIndicator = document.getElementById('typing-indicator');

let ws;

function connectWS() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        statusIndicator.classList.add('active');
        console.log('Connected to ZEUS backend.');
    };

    ws.onclose = () => {
        statusIndicator.classList.remove('active');
        setTimeout(connectWS, 2000);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Hide thinking animation
        typingIndicator.classList.add('hidden');

        appendMessage(data.response, 'bot', data.intent);

        if (data.audio_url) {
            ttsAudio.src = data.audio_url + '?t=' + Date.now();
            visualizer.classList.add('active');
            ttsAudio.play().catch(e => console.warn('Audio play failed:', e));
        }
    };
}

connectWS();
ttsAudio.onended = () => visualizer.classList.remove('active');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const PHASE_IDLE = 'idle';
    const PHASE_WAKE = 'wake';
    const PHASE_ACTIVE = 'active';

    let phase = PHASE_IDLE;
    let isListening = false;
    let retryTimeout = null;
    let silenceTimer = null;

    const wakeRec = new SpeechRecognition();
    wakeRec.continuous = true;
    wakeRec.interimResults = false;
    wakeRec.lang = 'en-US';

    const questionRec = new SpeechRecognition();
    questionRec.continuous = false;
    questionRec.interimResults = true;
    questionRec.lang = 'en-US';

    const clearSilenceTimer = () => { if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; } };
    const clearRetryTimeout = () => { if (retryTimeout) { clearTimeout(retryTimeout); retryTimeout = null; } };

    const startSilenceTimer = () => {
        clearSilenceTimer();
        silenceTimer = setTimeout(() => {
            statusText.innerText = "Timed out. Listening for 'Hey Nova'...";
            questionRec.stop();
            phase = PHASE_WAKE;
            micBtn.classList.remove('active-phase');
            micBtn.classList.add('listening');
        }, 7000);
    };

    const startWakeMode = () => {
        clearRetryTimeout();
        phase = PHASE_WAKE;
        try { wakeRec.start(); } catch (e) { }
    };

    const stopAll = () => {
        clearSilenceTimer(); clearRetryTimeout();
        phase = PHASE_IDLE; isListening = false;
        try { wakeRec.stop(); } catch (e) { }
        try { questionRec.stop(); } catch (e) { }
        micBtn.classList.remove('listening', 'active-phase');
        statusText.innerText = 'System asleep. Click mic to wake up.';
        if (ttsAudio.paused) visualizer.classList.remove('active');
    };

    micBtn.addEventListener('click', () => {
        if (phase === PHASE_IDLE) {
            startWakeMode();
            statusText.innerText = "Listening for 'Hey Nova'...";
            micBtn.classList.add('listening');
        } else {
            stopAll();
        }
    });

    wakeRec.onstart = () => { isListening = true; };

    wakeRec.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0]
            .transcript.trim().toLowerCase().replace(/[.,!?'"]/g, '');

        const WAKE_WORDS = ['hey nova', 'okay nova', 'nova', 'a nova', 'the nova', 'hey no va', 'k nova', 'aye nova'];
        const detected = WAKE_WORDS.some(w => transcript.includes(w));

        if (detected && phase === PHASE_WAKE) {
            phase = PHASE_ACTIVE;
            micBtn.classList.remove('listening');
            micBtn.classList.add('active-phase');
            statusText.innerText = 'NOVA activated — ask your question...';
            visualizer.classList.add('active');

            try { wakeRec.stop(); } catch (e) { }
            setTimeout(() => {
                try { questionRec.start(); } catch (e) { }
                startSilenceTimer();
            }, 300);
        }
    };

    wakeRec.onerror = (event) => {
        if (event.error === 'not-allowed') {
            stopAll(); statusText.innerText = 'Mic blocked. Allow in Chrome.';
        } else if (event.error !== 'aborted') {
            if (phase === PHASE_WAKE) retryTimeout = setTimeout(startWakeMode, 1000);
        }
    };

    wakeRec.onend = () => {
        isListening = false;
        if (phase === PHASE_WAKE) retryTimeout = setTimeout(startWakeMode, 300);
    };

    questionRec.onstart = () => { };

    questionRec.onresult = (event) => {
        startSilenceTimer();
        const result = event.results[event.results.length - 1];
        const transcript = result[0].transcript.trim();
        const isFinal = result.isFinal;

        statusText.innerText = 'Heard: ' + transcript;

        if (isFinal && transcript.length > 1) {
            clearSilenceTimer();
            appendMessage(transcript, 'user');
            visualizer.classList.add('active');

            if (ws && ws.readyState === WebSocket.OPEN) {
                // Show thinking animation
                typingIndicator.classList.remove('hidden');
                // Move indicator to bottom
                chatHistory.appendChild(typingIndicator);
                chatHistory.scrollTop = chatHistory.scrollHeight;

                ws.send(JSON.stringify({
                    text: transcript,
                    profile_id: profileSelect.value,
                }));
            } else {
                appendMessage('System offline. Start the backend.', 'bot', 'home');
            }

            phase = PHASE_WAKE;
            micBtn.classList.remove('active-phase');
            micBtn.classList.add('listening');
            statusText.innerText = "Listening for 'Hey Nova'...";
            setTimeout(() => { try { wakeRec.start(); } catch (e) { } }, 500);
        }
    };

    questionRec.onerror = (event) => {
        clearSilenceTimer();
        if (event.error === 'no-speech' || event.error === 'aborted') {
            phase = PHASE_WAKE;
            micBtn.classList.remove('active-phase');
            micBtn.classList.add('listening');
            statusText.innerText = "Listening for 'Hey Nova'...";
            retryTimeout = setTimeout(startWakeMode, 500);
        } else if (event.error === 'not-allowed') {
            stopAll();
        }
    };

    questionRec.onend = () => {
        if (phase === PHASE_ACTIVE) {
            retryTimeout = setTimeout(() => {
                try { questionRec.start(); } catch (e) { }
                startSilenceTimer();
            }, 300);
        }
    };

    statusText.innerText = 'Click the mic button to activate';

} else {
    statusText.innerText = 'Web Speech API not supported — use Chrome.';
    micBtn.style.opacity = '0.5';
    micBtn.style.cursor = 'not-allowed';
}

// ── UI helpers ───────────────────────────────────────────────────────────────
function appendMessage(text, sender, intent = null) {
    const div = document.createElement('div');
    div.classList.add('msg', sender);
    if (intent) div.classList.add(intent);

    const prefix = sender === 'bot' ? (intent === 'home' ? '🏠 ' : '✨ ') : '';
    div.innerText = prefix + text;

    // SAFE INSERTION LOGIC: 
    // Check if typing indicator is actually inside the chatHistory box right now
    if (typingIndicator.parentNode === chatHistory) {
        chatHistory.insertBefore(div, typingIndicator);
    } else {
        chatHistory.appendChild(div);
    }

    chatHistory.scrollTop = chatHistory.scrollHeight;
}