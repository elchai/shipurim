# Architecture Patterns — shipurim

Implementation patterns and gotchas. Use aliases from REGISTRY, never raw IDs.

## Live-transcribe — flow

```
Mic (sounddevice, 16kHz int16) → audio_queue
                                      ↓
                            send_audio coroutine
                                      ↓
                  base64 → WebSocket → ElevenLabs Scribe v2 Realtime
                                      ↓
                          receive_transcripts coroutine
                                      ↓
                  committed_transcript event → output_path.write_text(...)
                                      ↓
                       Claude Code reads on demand
```

הכל רץ בתוך coroutine אחד עם `asyncio.gather` של 3 לולאות (send / receive / reminder).
הפסקה דרך `asyncio.Event` שכל לולאה בודקת.

## Stop — 3 ערוצים

1. **Voice (fuzzy):** check_accumulated_stop בודק את 120 התווים האחרונים של ה-committed
   מול רשימת ביטויים, threshold 82 (rapidfuzz.partial_ratio).
2. **External flag file:** `%TEMP%\realtime-transcribe.stop` — אם קיים, set stop_event.
3. **PID file + Stop-Process:** ה-PowerShell script touch לקובץ ה-stop, מחכה 5s, ואז force-kill לפי PID.

## Windows-specific gotchas

- **אין `signal.SIGTERM`** — wrap ב-`if hasattr(signal, "SIGTERM"): try/except`.
- **asyncio loop policy** — websockets לא עובד טוב עם `ProactorEventLoop` (ברירת מחדל ב-Win).
  פתרון: `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())`.
- **UTF-8 stdio** — pythons ב-Windows יוצאים cp1252 ב-stdout/stderr. עברית תקרוס.
  פתרון: `sys.stderr.reconfigure(encoding="utf-8")` בראש הקובץ.
- **`afplay` לא קיים** — pygame.mixer.Sound() מקבלת MP3, ו-degrade gracefully אם pygame לא מותקן.
- **`/tmp` לא קיים** — `tempfile.gettempdir()` מחזיר `%TEMP%`. הכל דרך `pathlib.Path`.

## גישוּר Claude ↔ פגישה (התובנה המרכזית של הplugin)

הקובץ `%TEMP%\transcribe-*.txt` הוא **shared state** בין המיקרופון לסוכן.
הקובץ מתעדכן ב-append (ככה ש-Claude יכול לקרוא אותו תוך כדי) — כלומר Claude
לא מקבל push, אלא pull on demand. המשתמש יוזם את הקריאה ("בצע את מה שדיברנו").
זה הופך את הסוכן ל-actor אקטיבי באמצע הפגישה ולא post-mortem.
