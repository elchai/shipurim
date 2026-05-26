# shipurim — Live Transcribe (Windows port)

תמלול בזמן אמת מהמיקרופון שירד לקובץ טקסט על המחשב,
ונגיש לסשנים של **Claude Code** באמצע השיחה — בלי להמתין שהפגישה תסתיים.

הרעיון: סוכן שמקליט פגישה הוא נחמד; סוכן ש**מאזין בלייב** ויכול לבצע ברגע
את מה שהרגע סוכם בפגישה — זה אחר. הפלאגין הזה הוא הגישור: ElevenLabs Scribe v2 Realtime
דוחף טקסט לקובץ `%TEMP%\transcribe-*.txt`, וקלוד קורא אותו בכל רגע שתבקש.

> פורט Windows-native של [aviz85/claude-skills-library/plugins/live-transcribe](https://github.com/aviz85/claude-skills-library/tree/main/plugins/live-transcribe) (MIT).
> שינויים עיקריים: `%TEMP%` במקום `/tmp/`, `pygame.mixer` במקום `afplay`, PowerShell stop script, טיפול ב-SIGTERM שלא קיים ב-Windows.

## איך זה עובד

```
מיקרופון → sounddevice (PCM 16kHz) → base64 → WebSocket → ElevenLabs Scribe v2 Realtime
                                                                  ↓
                                                       committed_transcript
                                                                  ↓
                                                  %TEMP%\transcribe-{ts}.txt
                                                                  ↓
                                                        קלוד קורא on-demand
```

## דרישות

- **Windows 10/11** עם PowerShell 5.1+
- **Python 3.10+** ב-PATH (`python --version`)
- **ElevenLabs API key** עם גישה ל-Scribe (`elevenlabs.io`)
- **גישת מיקרופון** עבור הטרמינל / VS Code

## התקנה

```powershell
# 1) Clone (כבר עשית אם אתה קורא את זה מקומית)
git clone https://github.com/elchai/shipurim.git
cd shipurim

# 2) תלויות פייתון
pip install -r scripts/requirements.txt

# 3) ENV — הגדר את המפתח ב-User scope (זמין בכל הסשנים)
setx ELEVENLABS_API_KEY "sk_..."
# פתח טרמינל חדש כדי שה-setx ייכנס לתוקף

# 4) צלילי קיו (אופציונלי) — מייצר MP3s ב-assets/ עם הקול של ElevenLabs
python scripts/generate-sounds.py --lang he
# לאנגלית:  python scripts/generate-sounds.py --lang en
# קול מותאם: python scripts/generate-sounds.py --voice <VOICE_ID>
```

## הרצה כפלאגין Claude Code

הפרויקט כבר מבונה כפלאגין (`.claude-plugin/plugin.json` + `skills/`).
להתקנה ב-Claude Code שלך:

```
/plugin install file://C:/Users/User/Desktop/DEV/shipurim
```

או — אם אתה רק רוצה לנסות אותו בתוך הפרויקט הזה, ה-`skills/`
ייטענו אוטומטית כל סשן שתפתח בתיקייה.

## שימוש

### התחל תמלול
ב-Claude Code:
> "תתחיל לתמלל" / "start live transcription"

### קרא את התמלול תוך כדי / אחרי
> "מה אמרתי עכשיו?" / "תקרא את התמלול" / "סכם את מה שדיברנו"

### **הקילר**: בצע את מה שדובר עליו
> "תכין את הצעת המחיר שדיברנו עליה עכשיו ושלח בוואטסאפ ללקוח"
> — וקלוד יקרא את הקובץ, יסכם, ויפעל. הכל באמצע הפגישה.

### עצור
- **קול:** "אוקיי זה מספיק, בוא נעצור את התמלול" (fuzzy-matched HE+EN)
- **צ'אט:** "תעצור את התמלול"
- **ידני:** `New-Item -ItemType File -Path "$env:TEMP\realtime-transcribe.stop" -Force`

## הגדרות (env vars אופציונליים)

| משתנה                                | ברירת מחדל | תיאור                              |
|--------------------------------------|------------|------------------------------------|
| `ELEVENLABS_API_KEY`                 | (חובה)     | מפתח API של ElevenLabs             |
| `LIVE_TRANSCRIBE_LANG`               | `he`       | קוד שפה ISO 639-1                  |
| `LIVE_TRANSCRIBE_REMINDER_SECS`      | `1800`     | מרווח צליל תזכורת (30 דק)          |
| `LIVE_TRANSCRIBE_FUZZY_THRESHOLD`    | `82`       | רגישות זיהוי משפט עצירה (0-100)    |
| `LIVE_TRANSCRIBE_SOUNDS_DIR`         | `./assets` | תיקיית קבצי הקיו                   |

## פתרון בעיות

- **`ERROR: ELEVENLABS_API_KEY not set`** — הרצת `setx` ולא פתחת טרמינל חדש. פתח אחד.
- **`pygame.mixer unavailable`** — לא חובה, התמלול ירוץ בלי צלילים. `pip install pygame` אם רוצים.
- **PortAudio error / no input device** — תן ל-VS Code/לטרמינל הרשאת מיקרופון ב-Windows Settings → Privacy → Microphone.
- **הסקריפט קורס בלי לכתוב כלום** — הפעל ידנית `python scripts/realtime-transcribe.py` בטרמינל לראות את ה-stderr המלא.

## רישיון

MIT. מבוסס על [aviz85/live-transcribe](https://github.com/aviz85/claude-skills-library) (MIT).
