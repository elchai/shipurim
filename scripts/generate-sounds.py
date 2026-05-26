#!/usr/bin/env python3
"""
Generate the three audio cues (start / stop / reminder) using ElevenLabs TTS.
Outputs MP3s into ../assets/ next to the running script.

Usage:
    python generate-sounds.py
    python generate-sounds.py --voice VOICE_ID --lang he
    python generate-sounds.py --lang en
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs "Rachel" — sane default
DEFAULT_MODEL = "eleven_multilingual_v2"

CUES = {
    "he": {
        "start":    "התחלתי תמלול!",
        "stop":     "סיימתי את התמלול",
        "reminder": "עדיין מתמלל...",
    },
    "en": {
        "start":    "Started transcribing!",
        "stop":     "Stopped transcribing.",
        "reminder": "Still transcribing...",
    },
}


def tts(api_key: str, voice_id: str, text: str, model: str, out_path: Path) -> None:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    body = json.dumps({"text": text, "model_id": model}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ElevenLabs TTS failed ({e.code}): {err_body}") from e

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print(f"  wrote {out_path}  ({len(data):,} bytes)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate live-transcribe audio cues via ElevenLabs.")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help="ElevenLabs voice ID")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="ElevenLabs model ID")
    ap.add_argument("--lang",  default="he", choices=list(CUES.keys()), help="Cue language")
    ap.add_argument("--out",   default=None, help="Output dir (default: ../assets/)")
    args = ap.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "assets"
    print(f"Generating {args.lang} cues into {out_dir} (voice={args.voice}, model={args.model})")
    for name, text in CUES[args.lang].items():
        tts(api_key, args.voice, text, args.model, out_dir / f"{name}.mp3")
    print("Done.")


if __name__ == "__main__":
    main()
