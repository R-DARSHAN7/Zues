const chatHistory = document.getElementById('chat-history');
const micBtn = document.getElementById('mic-btn');
const statusText = document.getElementById('status-text');
const visualizer = document.getElementById('audio-visualizer');
const ttsAudio = document.getElementById('tts-audio');
const statusIndicator = document.querySelector('.status-indicator');
const profileSelect = document.getElementById('profile-select');

// ── WebSocket ────────────────────────────────────────────────────────────────
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

// ── Speech Recognition ───────────────────────────────────────────────────────
const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {

    // ── State ────────────────────────────────────────────────────────────────
    const PHASE_IDLE = 'idle';       // mic off, user hasn't clicked yet
    const PHASE_WAKE = 'wake';       // listening for "Hey Zeus" only
    const PHASE_ACTIVE = 'active';     // wake word heard, listening for question

    let phase = PHASE_IDLE;
    let isListening = false;
    let retryTimeout = null;
    let silenceTimer = null;            // 7 second timeout in active phase

    // ── Two recognizer instances ─────────────────────────────────────────────
    // Wake recognizer — always on, short phrases
    const wakeRec = new SpeechRecognition();
    wakeRec.continuous = true;
    wakeRec.interimResults = false;
    wakeRec.lang = 'en-US';

    // Question recognizer — turns on after wake word
    const questionRec = new SpeechRecognition();
    questionRec.continuous = false;  // captures one full question
    questionRec.interimResults = true;   // shows text appearing live
    questionRec.lang = 'en-US';

    // ── Helpers ──────────────────────────────────────────────────────────────
    const clearSilenceTimer = () => {
        if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
    };

    const clearRetryTimeout = () => {
        if (retryTimeout) { clearTimeout(retryTimeout); retryTimeout = null; }
    };

    const startSilenceTimer = () => {
        clearSilenceTimer();
        silenceTimer = setTimeout(() => {
            // No question asked in 7 seconds — go back to wake mode
            console.log('7s silence — returning to wake mode.');
            statusText.innerText = "Timed out. Listening for 'Hey Zeus'...";
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
        clearSilenceTimer();
        clearRetryTimeout();
        phase = PHASE_IDLE;
        isListening = false;
        try { wakeRec.stop(); } catch (e) { }
        try { questionRec.stop(); } catch (e) { }
        micBtn.classList.remove('listening', 'active-phase');
        statusText.innerText = 'System asleep. Click mic to wake up.';
        if (ttsAudio.paused) visualizer.classList.remove('active');
    };

    // ── Mic button toggle ────────────────────────────────────────────────────
    micBtn.addEventListener('click', () => {
        if (phase === PHASE_IDLE) {
            startWakeMode();
            statusText.innerText = "Listening for 'Hey Zeus'...";
            micBtn.classList.add('listening');
        } else {
            stopAll();
        }
    });

    // ── Wake recognizer events ───────────────────────────────────────────────
    wakeRec.onstart = () => {
        isListening = true;
        console.log('Wake mode active.');
    };

    wakeRec.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0]
            .transcript.trim().toLowerCase().replace(/[.,!?'"]/g, '');

        console.log('Wake heard:', transcript);

        const wakeWords = [
            'hey zeus', 'hey zoos', 'hey juice',
            'hey jesus', 'hey ze', 'zeus'
        ];
        const detected = wakeWords.some(w => transcript.includes(w));

        if (detected && phase === PHASE_WAKE) {
            console.log('Wake word detected — switching to active mode.');
            phase = PHASE_ACTIVE;

            // Visual feedback
            micBtn.classList.remove('listening');
            micBtn.classList.add('active-phase');
            statusText.innerText = 'ZEUS activated — ask your question...';
            visualizer.classList.add('active');

            // Stop wake recognizer, start question recognizer
            try { wakeRec.stop(); } catch (e) { }

            setTimeout(() => {
                try { questionRec.start(); } catch (e) { }
                startSilenceTimer();
            }, 300);
        }
    };

    wakeRec.onerror = (event) => {
        console.warn('Wake error:', event.error);
        if (event.error === 'not-allowed') {
            stopAll();
            statusText.innerText = 'Mic blocked. Allow in Chrome settings.';
        } else if (event.error !== 'aborted') {
            if (phase === PHASE_WAKE) {
                retryTimeout = setTimeout(startWakeMode, 1000);
            }
        }
    };

    wakeRec.onend = () => {
        isListening = false;
        console.log('Wake recognizer ended. Phase:', phase);
        if (phase === PHASE_WAKE) {
            // Keep wake mode alive
            retryTimeout = setTimeout(startWakeMode, 300);
        }
    };

    // ── Question recognizer events ───────────────────────────────────────────
    questionRec.onstart = () => {
        console.log('Question mode active — waiting for question.');
    };

    questionRec.onresult = (event) => {
        // Reset silence timer every time speech is detected
        startSilenceTimer();

        const result = event.results[event.results.length - 1];
        const transcript = result[0].transcript.trim();
        const isFinal = result.isFinal;

        // Show live transcript while speaking
        statusText.innerText = 'Heard: ' + transcript;

        if (isFinal && transcript.length > 1) {
            console.log('Question captured:', transcript);
            clearSilenceTimer();

            appendMessage(transcript, 'user');
            visualizer.classList.add('active');

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    text: transcript,
                    profile_id: profileSelect.value,
                }));
            } else {
                appendMessage('System offline. Start the backend.', 'bot', 'home');
            }

            // Go back to wake mode after sending
            phase = PHASE_WAKE;
            micBtn.classList.remove('active-phase');
            micBtn.classList.add('listening');
            statusText.innerText = "Listening for 'Hey Zeus'...";
            setTimeout(() => {
                try { wakeRec.start(); } catch (e) { }
            }, 500);
        }
    };

    questionRec.onerror = (event) => {
        console.warn('Question error:', event.error);
        clearSilenceTimer();
        if (event.error === 'no-speech' || event.error === 'aborted') {
            // Timeout or abort — go back to wake mode
            phase = PHASE_WAKE;
            micBtn.classList.remove('active-phase');
            micBtn.classList.add('listening');
            statusText.innerText = "Listening for 'Hey Zeus'...";
            retryTimeout = setTimeout(startWakeMode, 500);
        } else if (event.error === 'not-allowed') {
            stopAll();
        }
    };

    questionRec.onend = () => {
        console.log('Question recognizer ended. Phase:', phase);
        if (phase === PHASE_ACTIVE) {
            // Ended without capturing — restart question mode
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

    const prefix = sender === 'bot'
        ? (intent === 'home' ? '🏠 ' : '📚 ')
        : '';

    div.innerText = prefix + text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}