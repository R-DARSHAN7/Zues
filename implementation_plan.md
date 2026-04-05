# ZEUS v1 AI Assistant

This document outlines the architecture and implementation plan for ZEUS v1, a voice-activated AI assistant designed for education and smart home control.

## User Review Required

> [!WARNING]
> Please review the audio processing architecture. We have two options for the microphone input:
> 1. **Local Server Mic**: The Python server directly listens to the host machine's microphone using `pvporcupine` for the wake word and streams to Whisper.
> 2. **Browser-based Mic**: The Web UI captures audio via the browser and streams it over WebSockets to the Python server for wake-word detection and STT.
> *Since ZEUS is meant to be accessible on the home network, the browser approach allows any device to be a client. Alternatively, both can exist. How would you like "Hey Zeus" to trigger? From the main computer running the server natively, or from any browser window that stays open on the network, or both?*

> [!IMPORTANT]
> **Google Home Integration**: Interacting natively with Google Home to control devices typically requires a linked action via Google Cloud Console, or an intermediary like Home Assistant. For V1, I will build an abstraction layer for Home Control that can trigger custom REST requests or integrate with `google-nest-sdks`. Do you have an existing Smart Home hub (like Home Assistant), or do you want to rely purely on official Google Home SDK/APIs (which may need GCP project setup)?

## Proposed Architecture

The system will connect a backend **FastAPI** service with a **Web UI** built dynamically:

1. **Audio Pipeline (Input)**:
   - WebSocket endpoint taking raw audio chunks.
   - Wake Word Engine (`pvporcupine`) to detect "Hey Zeus".
   - STT Engine (`whisper` or faster-whisper natively for offline processing).
2. **Brain Core & Router**:
   - Intent Router to determine if an utterance is an Education or Home command.
   - LLM Engine (Interface supporting `OpenAI GPT-4o-mini` and `Ollama` local models).
   - Profile Manager (SQLite) to identify the family member (simple pin/web profile selection for now) and retrieve chat history/preferences.
3. **Domain Engines**:
   - **Education Engine**: Specialized prompts and state management for Q&A, Quizzes, Flashcards, Exam prep, and Career guidance.
   - **Home Engine**: Abstraction layer mapping natural language ("turn off bedroom lights") to device API commands.
4. **Audio Pipeline (Output)**:
   - TTS Engine dynamically swapping between `ElevenLabs` (premium voice) and `pyttsx3` (fallback/offline).
5. **Web Interface**:
   - Built with HTML, Vanilla CSS, and JS (No heavy framework, served statically via FastAPI).
   - **Stunning UI**: Premium glassmorphism, glowing audio visualizers, vibrant dark mode.
   - Responsive UI accessible from any mobile device or tablet on the local network.

---

## Proposed Changes

### Core API & Web Server

#### [NEW] `c:\Zues\main.py`
The FastAPI application, mounting static files, adding a REST API for profile/chat history, and setting up WebSocket routes for audio streaming.

#### [NEW] `c:\Zues\requirements.txt`
Dependencies (FastAPI, uvicorn, PyAudio, pvporcupine, openai-whisper, openai, pyttsx3, elevenlabs, sqlalchemy).

### Audio Pipeline

#### [NEW] `c:\Zues\backend\audio\wake_word.py`
Integration with `pvporcupine` for accurate and lightweight trigger word tracking.

#### [NEW] `c:\Zues\backend\audio\stt.py`
Integration with offline Whisper model.

#### [NEW] `c:\Zues\backend\audio\tts.py`
Voice synthesis switching between ElevenLabs API and `pyttsx3`.

### LLM & Routing

#### [NEW] `c:\Zues\backend\brain\router.py`
Determines if an utterance is meant for Home Control or standard LLM queries (Education/General).

#### [NEW] `c:\Zues\backend\brain\llm_client.py`
Unified LLM interface supporting both `GPT-4o-mini` and `Ollama` local models depending on config.

#### [NEW] `c:\Zues\backend\core\config.py` & `database.py`
Pydantic BaseSettings to handle `.env` variables and SQLite database definitions.

### Web Server & UI

#### [NEW] `c:\Zues\static\index.html`
Premium UI dashboard acting as the main interface.

#### [NEW] `c:\Zues\static\style.css`
Advanced vanilla CSS utilizing CSS vars, glassmorphic panels, dynamic animations, and responsive layouts.

#### [NEW] `c:\Zues\static\app.js`
WebSocket frontend handling capturing microphone audio, providing visualizer feedback, playing returned TTS audio, and managing the chat/study states.

## Verification Plan

### Automated/Manual Verification
1. Verify API setup with `uvicorn main:app --reload`.
2. Ensure local microphone streams via WebSocket effectively trigger Porcupine.
3. Verify routing works for "turn off the living room lights" (Home Control Domain) vs "quiz me on mitosis" (Education Domain).
4. Verify the web interface displays elegantly on desktop and mimics a premium app on mobile browsers.
