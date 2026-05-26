---
name: live-transcribe-read
description: "Read the latest real-time transcription. Use when user asks to see, read, summarize, translate, or act on a transcription captured via live-transcribe. Triggers on: 'read the transcription', 'show transcript', 'what did I say', 'summarize what I said', 'תקרא את התמלול', 'מה אמרתי עכשיו', 'בצע את מה שדיברנו'."
---

# Live Transcribe — Read (Windows)

Read the most recent transcript file from a live-transcribe session.
The transcript updates in real time — it's safe to read while transcription is still running.

## Find the latest transcript

```powershell
Get-ChildItem -Path $env:TEMP -Filter 'transcribe-*.txt' -File `
    | Sort-Object LastWriteTime -Descending `
    | Select-Object -First 1 -ExpandProperty FullName
```

The naming convention is `%TEMP%\transcribe-YYYYMMDD-HHMMSS.txt`.

## Read its contents

```powershell
Get-Content -Path '<path-from-above>' -Encoding UTF8 -Raw
```

## Check whether transcription is still active

```powershell
$pidFile = Join-Path $env:TEMP 'realtime-transcribe.pid'
if (Test-Path $pidFile) {
    $pidValue = Get-Content $pidFile | Select-Object -First 1
    if ($pidValue -and (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
        'ACTIVE'
    } else { 'FINISHED' }
} else { 'FINISHED' }
```

## What to tell the user

1. The transcription text (verbatim if short, summarized if asked)
2. Whether it's still being updated (ACTIVE) or finished (FINISHED)
3. If no `transcribe-*.txt` files exist: no transcription has been recorded yet — offer to start one

## Acting on the transcript

When the user says things like "do what we just talked about" or "execute that", treat the transcript
as a directive: re-read it, summarize the request in your head, confirm intent in one sentence, and act.
The transcript captures **what was said in the meeting** — the user is your interface, not the meeting audio.
