# הנחיות עבור Claude Code

- שפת תקשורת: עברית
- זיכרון מתמשך נמצא ב-.claude/memory/:
  - REGISTRY.md — IDs, מפתחות, URLs, webhooks
  - ARCH_PATTERNS.md — דפוסי תכנון וגוטצ'אז (השתמש בכינויים מ-REGISTRY, לא ב-IDs גולמיים)
  - CURRENT_SPRINT.md — מה עובדים עליו כרגע
- לפני כל סשן: קרא את CURRENT_SPRINT.md
- לפני שימוש ב-ID/מפתח: בדוק את REGISTRY.md
- בסוף סשן משמעותי: הפעל `/burn` לחילוץ ידע חדש

## על הפרויקט
- **מהות:** Windows port של plugin live-transcribe (aviz85, MIT). תמלול בזמן אמת מהמיקרופון
  ל-`%TEMP%\transcribe-*.txt`, וקלוד קורא תוך כדי הסשן.
- **מבנה:**
  - `scripts/realtime-transcribe.py` — הליבה. WebSocket ל-ElevenLabs Scribe v2 Realtime.
  - `scripts/stop-transcribe.ps1` — עצירה graceful עם fallback ל-force-kill.
  - `scripts/generate-sounds.py` — מייצר MP3s ל-`assets/` דרך ElevenLabs TTS.
  - `skills/live-transcribe{,-read,-stop}/SKILL.md` — שלוש כניסות.
  - `.claude-plugin/plugin.json` — מטא של פלאגין Claude Code.
- **תלויות runtime:** `pip install -r scripts/requirements.txt`
  (sounddevice, websockets, numpy, rapidfuzz, pygame).
- **מפתח:** `ELEVENLABS_API_KEY` חייב להיות מוגדר בסביבה. עדיף `setx` ל-User scope.

## גוטצ'אז Windows-specific (חשוב לזכור)
- ב-Windows אין `SIGTERM` — הסקריפט עוטף ב-try/except. אל תוסיף תלות בזה.
- `websockets` ב-Windows צריך `WindowsSelectorEventLoopPolicy` (כבר מוגדר ב-main).
- ב-PowerShell אין `&&` ב-5.1 — השתמש ב-`if ($?) { ... }` או `;`.
- stdout/stderr — דחיתי ל-UTF-8 בהתחלת הסקריפט כדי שעברית לא תקרוס על cp1252.
- `setx` משפיע רק על טרמינלים **חדשים**. אם המפתח לא מוכר — לפתוח טרמינל חדש.
