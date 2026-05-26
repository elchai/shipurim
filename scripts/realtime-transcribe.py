#!/usr/bin/env python3
"""
Realtime transcription via ElevenLabs Scribe v2 Realtime WebSocket API.
Windows-native adaptation of aviz85/live-transcribe (MIT).

Captures microphone audio, streams to ElevenLabs, writes transcript to a temp file.
Supports fuzzy stop-phrase detection (HE+EN) and external stop via file flag.
"""

import asyncio
import base64
import io
import json
import os
import signal
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import websockets
from rapidfuzz import fuzz

# --- Windows: force UTF-8 stderr so Hebrew prints don't crash on cp1252 ---
if sys.platform == "win32":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # websockets needs a Selector loop, not Proactor, on Windows for some setups
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass

# --- Optional audio playback (pygame.mixer). Degrades to silent if unavailable. ---
try:
    import pygame
    pygame.mixer.init()
    _AUDIO_OK = True
except Exception as _e:
    _AUDIO_OK = False
    print(f"[audio] pygame.mixer unavailable, cues disabled: {_e}", file=sys.stderr)

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"

# Sounds dir: env override > plugin's assets/ next to scripts/
_DEFAULT_SOUNDS = Path(__file__).resolve().parent.parent / "assets"
SOUNDS_DIR = Path(os.environ.get("LIVE_TRANSCRIBE_SOUNDS_DIR", str(_DEFAULT_SOUNDS)))

# Temp dir: cross-platform (Windows: %TEMP%, *nix: /tmp)
TEMP_DIR = Path(tempfile.gettempdir())
PID_FILE = TEMP_DIR / "realtime-transcribe.pid"
STOP_FILE = TEMP_DIR / "realtime-transcribe.stop"
LOG_FILE = TEMP_DIR / "realtime-transcribe.log"  # informational only

REMINDER_INTERVAL_SECS = int(os.environ.get("LIVE_TRANSCRIBE_REMINDER_SECS", "1800"))  # 30 min
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION_MS = 100
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)

# Stop phrases — fuzzy-matched against the tail of the committed transcript.
STOP_PHRASES = [
    "אוקי זה מספיק בוא נעצור את התמלול",
    "אוקיי זה מספיק בוא נעצור את התימלול",
    "בוא נעצור את התמלול",
    "עצור תמלול",
    "stop transcription",
    "ok stop transcribing",
]
FUZZY_THRESHOLD = int(os.environ.get("LIVE_TRANSCRIBE_FUZZY_THRESHOLD", "82"))

LANGUAGE_CODE = os.environ.get("LIVE_TRANSCRIBE_LANG", "he")


def play_sound(name: str, wait: bool = False) -> None:
    """Play a pre-recorded audio cue (mp3 or wav). Silent no-op if pygame missing or file absent."""
    if not _AUDIO_OK:
        return
    for ext in (".mp3", ".wav"):
        sound_file = SOUNDS_DIR / f"{name}{ext}"
        if sound_file.exists():
            try:
                snd = pygame.mixer.Sound(str(sound_file))
                ch = snd.play()
                if wait and ch is not None:
                    while ch.get_busy():
                        time.sleep(0.05)
            except Exception as e:
                print(f"[audio] failed to play {sound_file.name}: {e}", file=sys.stderr)
            return


def get_output_path() -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return TEMP_DIR / f"transcribe-{ts}.txt"


def write_pid() -> None:
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def cleanup_pid() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass
    try:
        STOP_FILE.unlink()
    except FileNotFoundError:
        pass


def should_stop_external() -> bool:
    return STOP_FILE.exists()


def check_accumulated_stop(full_text: str) -> bool:
    """Look at the last ~120 chars of the committed transcript for any stop phrase."""
    tail = full_text[-120:].strip().lower() if len(full_text) > 10 else ""
    if not tail:
        return False
    for phrase in STOP_PHRASES:
        if fuzz.partial_ratio(tail, phrase.lower()) >= FUZZY_THRESHOLD:
            return True
    return False


async def main() -> None:
    if not API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    output_path = get_output_path()
    output_path.write_text("", encoding="utf-8")
    write_pid()
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    # First line of stdout/log: JSON startup record. Skill reads this.
    print(json.dumps({
        "status": "started",
        "pid": os.getpid(),
        "output_file": str(output_path),
        "pid_file": str(PID_FILE),
        "stop_file": str(STOP_FILE),
    }))
    sys.stdout.flush()

    stop_event = asyncio.Event()
    audio_queue: asyncio.Queue = asyncio.Queue()
    committed_text_parts: list[str] = []
    current_partial = ""

    def signal_handler(sig, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM doesn't exist on Windows
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, AttributeError):
            pass

    def audio_callback(indata, frames, time_info, status):
        if status:
            pass  # ignore overflow
        audio_queue.put_nowait(indata.copy())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=CHUNK_SAMPLES,
        callback=audio_callback,
    )

    ws_params = {
        "model_id": "scribe_v2_realtime",
        "audio_format": f"pcm_{SAMPLE_RATE}",
        "commit_strategy": "vad",
        "language_code": LANGUAGE_CODE,
        "include_timestamps": "false",
        "no_verbatim": "false",
    }
    query = "&".join(f"{k}={v}" for k, v in ws_params.items())
    url = f"{WS_URL}?{query}"
    headers = {"xi-api-key": API_KEY}

    try:
        async with websockets.connect(url, additional_headers=headers, ping_interval=20) as ws:
            play_sound("start", wait=True)
            stream.start()
            print("Recording... speak now.", file=sys.stderr)

            async def reminder_loop():
                while not stop_event.is_set():
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=REMINDER_INTERVAL_SECS)
                        break
                    except asyncio.TimeoutError:
                        play_sound("reminder")
                        print("[reminder] still transcribing...", file=sys.stderr)

            async def send_audio():
                while not stop_event.is_set():
                    try:
                        chunk = await asyncio.wait_for(audio_queue.get(), timeout=0.2)
                    except asyncio.TimeoutError:
                        if should_stop_external():
                            play_sound("stop")
                            stop_event.set()
                        continue

                    pcm_bytes = chunk.tobytes()
                    b64 = base64.b64encode(pcm_bytes).decode("ascii")
                    msg = {
                        "message_type": "input_audio_chunk",
                        "audio_base_64": b64,
                        "sample_rate": SAMPLE_RATE,
                    }
                    try:
                        await ws.send(json.dumps(msg))
                    except websockets.exceptions.ConnectionClosed:
                        stop_event.set()
                        break

                    if should_stop_external():
                        stop_event.set()

            async def receive_transcripts():
                nonlocal current_partial
                while not stop_event.is_set():
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        stop_event.set()
                        break

                    data = json.loads(raw)
                    msg_type = data.get("message_type", "")

                    if msg_type == "partial_transcript":
                        current_partial = data.get("text", "")

                    elif msg_type in ("committed_transcript", "committed_transcript_with_timestamps"):
                        text = data.get("text", "").strip()
                        if text:
                            committed_text_parts.append(text)
                            current_partial = ""
                            full = " ".join(committed_text_parts)
                            output_path.write_text(full, encoding="utf-8")
                            print(f"[committed] {text}", file=sys.stderr)

                            if check_accumulated_stop(full):
                                print("[stop phrase detected]", file=sys.stderr)
                                play_sound("stop")
                                stop_event.set()
                                break

                    elif msg_type == "session_started":
                        print("[session started]", file=sys.stderr)

                    elif "error" in msg_type:
                        print(f"[error] {data}", file=sys.stderr)
                        stop_event.set()
                        break

            await asyncio.gather(send_audio(), receive_transcripts(), reminder_loop())

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
        full_text = " ".join(committed_text_parts)
        output_path.write_text(full_text, encoding="utf-8")
        cleanup_pid()
        print(f"Transcription saved to {output_path}", file=sys.stderr)
        print(json.dumps({
            "status": "stopped",
            "output_file": str(output_path),
            "words": len(full_text.split()),
        }))


if __name__ == "__main__":
    asyncio.run(main())
