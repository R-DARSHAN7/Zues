import os
import tempfile
import numpy as np
from faster_whisper import WhisperModel


class STTEngine:
    def __init__(self):
        print("Loading Whisper base model...")
        self.whisper = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

        print("Loading Silero VAD...")
        import torch
        from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
        self.torch = torch
        self.load_silero_vad = load_silero_vad
        self.read_audio = read_audio
        self.get_speech_timestamps = get_speech_timestamps
        self.vad_model = load_silero_vad()
        print("VAD ready.")
        print("STT Engine fully loaded.")

    def _has_speech(self, audio_path: str) -> bool:
        """
        Returns True if Silero VAD detects actual speech in the audio.
        Filters out background TV, noise, silence.
        """
        try:
            wav = self.read_audio(audio_path, sampling_rate=16000)
            timestamps = self.get_speech_timestamps(
                wav,
                self.vad_model,
                threshold=0.4,        # 0.0-1.0, higher = stricter
                sampling_rate=16000,
                min_speech_duration_ms=300,   # ignore very short sounds
                min_silence_duration_ms=100,
            )
            speech_duration = sum(
                t['end'] - t['start'] for t in timestamps
            ) / 16000  # convert samples to seconds

            print(f"VAD: {len(timestamps)} speech segments, "
                  f"{speech_duration:.1f}s of speech detected")

            return speech_duration > 0.3  # at least 0.3s of real speech
        except Exception as e:
            print(f"VAD error: {e}")
            return True  # if VAD fails, let Whisper try anyway

    def transcribe(self, audio_bytes: bytes) -> str:
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            suffix=".webm", delete=False
        ) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Step 1 — Convert webm to wav for VAD
            wav_path = tmp_path.replace(".webm", ".wav")
            os.system(
                f'ffmpeg -i "{tmp_path}" -ar 16000 -ac 1 '
                f'-f wav "{wav_path}" -y -loglevel quiet'
            )

            # Step 2 — VAD check — is there real speech?
            if os.path.exists(wav_path):
                has_speech = self._has_speech(wav_path)
                if not has_speech:
                    print("VAD: No real speech detected — ignoring audio.")
                    return ""
            else:
                print("WAV conversion failed — skipping VAD.")
                wav_path = None

            # Step 3 — Whisper transcription
            transcribe_path = wav_path if wav_path else tmp_path
            segments, info = self.whisper.transcribe(
                transcribe_path,
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
                initial_prompt="Nova",
                vad_filter=True,          # Whisper's built-in VAD too
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    threshold=0.4,
                ),
            )
            text = " ".join(seg.text.strip() for seg in segments)
            return text.strip()

        finally:
            # Cleanup temp files
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            try:
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except OSError:
                pass