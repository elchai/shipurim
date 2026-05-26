# Current Sprint — shipurim

## Active work
- **Live-transcribe Windows port** — v0.1.0 פורסם מ-aviz85 plugin (MIT).
- מבנה: Claude Code plugin (`.claude-plugin/plugin.json` + `skills/` + `scripts/`).

## TODO לפני יציאה לפועל
- [ ] לוודא ש-`ELEVENLABS_API_KEY` מוגדר עם `setx` ב-User scope
- [ ] `pip install -r scripts/requirements.txt` בסביבה הנכונה
- [ ] להריץ `python scripts/generate-sounds.py --lang he` ליצירת קיוים בעברית
- [ ] בדיקת end-to-end: התחל → דבר → קרא transcript → עצור
- [ ] אם הכל עובד — push לגיט elchai/shipurim

## רעיונות לעתיד (לא ממומשים)
- **Voice trigger לסוכן ברקע** ("סוכן יקר בבקשה תבצע") — הפעלת Agent SDK אוטומטית.
  הוחלט לדחות כי זה מסוכן ודורש confirmation אנושי.
- **חלוקה לפי דובר** (speaker diarization) — Scribe v2 לא תומך לייב, רק batch.
