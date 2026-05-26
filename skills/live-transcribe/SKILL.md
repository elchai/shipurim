---
name: live-transcribe
description: "Start real-time microphone transcription using ElevenLabs Scribe v2 Realtime. Use when user wants to start live transcription, dictation, or real-time speech capture. Triggers on: 'start transcribing', 'live transcribe', 'record what I say', 'תתחיל לתמלל', 'תמלל את מה שאני אומר'. After starting, tell user they can say 'אוקיי זה מספיק בוא נעצור את התמלול' to stop via voice, or use /live-transcribe-stop."
---

# Live Transcribe — Start (Windows)

Start real-time microphone transcription via ElevenLabs Scribe v2 Realtime WebSocket API.
Audio streams to ElevenLabs; committed transcript is written to a file under `%TEMP%`
that you can read at any time during the session.

## Before starting — check nothing is already running

```powershell
$pidFile = Join-Path $env:TEMP 'realtime-transcribe.pid'
if (Test-Path $pidFile) {
    $pidValue = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pidValue -and (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
        'ALREADY RUNNING'
    } else {
        Remove-Item $pidFile -Force
        'stale-pid-cleaned'
    }
} else { 'NONE' }
```

If `ALREADY RUNNING`, tell the user and offer to stop the existing session first.

## Start command

The plugin lives at `${CLAUDE_PLUGIN_ROOT}` (or this project's root if running locally).
Spawn the Python script in the background using `run_in_background: true` on your Bash tool call:

```powershell
$env:ELEVENLABS_API_KEY = $env:ELEVENLABS_API_KEY  # ensure inherited
python "${CLAUDE_PLUGIN_ROOT}\scripts\realtime-transcribe.py"
```

Then wait ~3 seconds and read the **first line** of the background output — it's a JSON record:

```json
{"status": "started", "pid": 12345, "output_file": "C:\\Users\\...\\AppData\\Local\\Temp\\transcribe-20260526-143022.txt", "pid_file": "...", "stop_file": "..."}
```

If the script aborts immediately, check for `ERROR: ELEVENLABS_API_KEY not set` — that's the common cause.

## Audio cues

If `assets/start.mp3` / `stop.mp3` / `reminder.mp3` exist (generate with `python scripts/generate-sounds.py`),
the script plays them automatically:
- **start** — before recording begins (waited)
- **stop** — when transcription ends (any path)
- **reminder** — every 30 minutes while still active

Missing files = silent no-op, not an error.

## What to return to the user

1. The `output_file` path (so they know where the transcript lives)
2. That transcription is running and they can keep talking
3. Three ways to stop:
   - **Voice:** say "אוקיי זה מספיק בוא נעצור את התמלול" (fuzzy-matched HE+EN)
   - **Chat:** ask me to stop the transcription (triggers `live-transcribe-stop`)
   - **Manual:** ``New-Item -ItemType File -Path (Join-Path $env:TEMP 'realtime-transcribe.stop') -Force``
