---
name: live-transcribe-stop
description: "Stop a running real-time transcription. Use when user wants to stop, end, halt, or finish live transcription. Triggers on: 'stop transcription', 'end transcription', 'stop recording', 'תעצור את התמלול', 'סיים תמלול'."
---

# Live Transcribe — Stop (Windows)

Stop a running real-time transcription session gracefully.

## Stop command (preferred)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}\scripts\stop-transcribe.ps1"
```

The script touches `%TEMP%\realtime-transcribe.stop`, waits up to 5 seconds for graceful exit,
and force-kills the Python process if it didn't shut down cleanly.

## Fallback (manual flag)

If the helper script is unavailable:

```powershell
New-Item -ItemType File -Path (Join-Path $env:TEMP 'realtime-transcribe.stop') -Force | Out-Null
```

The running script checks this flag every ~200 ms and exits cleanly when it sees it.

## After stopping

Show the final transcript path:

```powershell
Get-ChildItem -Path $env:TEMP -Filter 'transcribe-*.txt' -File `
    | Sort-Object LastWriteTime -Descending `
    | Select-Object -First 1 -ExpandProperty FullName
```

Then offer to read it (delegates to `live-transcribe-read`).
