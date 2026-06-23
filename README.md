# Doomless — Beat the Scroll

> You have free time. Use it well. Stop doomscrolling. Start doing.

Doomless is a productivity app that suggests one focused activity based on your interests and available time. Built in a single night hackathon sprint.

---

## What It Does

1. **Set your time** — tell the app how many minutes you have free
2. **Pick interests** — select what you're into (guitar, cooking, photography, etc.)
3. **Get a suggestion** — Groq AI suggests one specific, focused activity
4. **Commit** — a timer locks you in. No scrolling. Just do it.
5. **Log it** — activity is saved to Postgres and synced to Google Sheets

---

## Stack

| Layer | Tech | Why |
|-------|------|-----|
| Backend | Python + Flask | Simple HTTP server with clean routes |
| Database | PostgreSQL | Stores users, interests, activity logs |
| AI | Groq API (llama-3.1-8b-instant) | Fast, free-tier LLM for activity suggestions |
| Frontend | Vanilla HTML + CSS + JS | Zero dependencies, no build step |
| Sync | Google Sheets via Apps Script | Automatic activity backup |

---

## Project Structure

```
doomless/
├── backend/
│   ├── server.py        — Flask server, all routes
│   └── server.awk       — original Awk server (archived)
├── db/
│   ├── schema.sql       — tables: users, interests, activity_log
│   ├── functions.sql    — stored procedures
│   └── seed.sql         — sample interests for testing
├── frontend/
│   ├── index.html       — landing page + stats
│   ├── suggest.html     — activity suggestion + timer
│   ├── interests.html   — interests checklist
│   ├── history.html     — past activities log
│   └── style.css        — one CSS file, Candlelit Scholar palette
├── gemini/
│   ├── prompt.txt       — base prompt template
│   └── call.sh          — curl wrapper (archived)
├── sheets/
│   └── sheets.sh        — Google Sheets sync script
├── .env.example         — environment variable template
├── .gitignore
└── README.md
```

---

## Architecture

```
Browser (HTML/CSS/JS)
        ↓ fetch()
Flask Server (port 8080)
        ↓                    ↓
  PostgreSQL DB         Groq API
  (interests,           (llama-3.1-8b)
   activity_log)
        ↓
  Google Sheets
  (Apps Script webhook)
```

---

## How to Run

### 1. Prerequisites

```bash
# Install dependencies
sudo apt install postgresql python3-pip
pip3 install flask --break-system-packages
```

### 2. Set up PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE doomless;
\q

sudo -u postgres psql -d doomless -f db/schema.sql

# Create a user
sudo -u postgres psql -d doomless -c "INSERT INTO users (id, name) VALUES (1, 'yourname');"
```

### 3. Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in:
```
GROQ_API_KEY=your_groq_key_here
SHEETS_URL=your_apps_script_webhook_url
```

Get a free Groq API key at: https://console.groq.com

### 4. Set up Google Sheets (optional)

1. Create a new Google Sheet at https://sheets.google.com
2. Go to Extensions → Apps Script
3. Paste this code:

```javascript
function doPost(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = JSON.parse(e.postData.contents);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['User ID', 'Activity', 'Time Spent (min)', 'Logged At']);
  }
  sheet.appendRow([data.user_id, data.activity, data.time_spent, data.logged_at]);
  return ContentService.createTextOutput(JSON.stringify({status: 'ok'}))
    .setMimeType(ContentService.MimeType.JSON);
}
```

4. Deploy as Web App → Execute as Me → Anyone can access
5. Copy the webhook URL into `.env` as `SHEETS_URL`

### 5. Allow passwordless postgres access

```bash
sudo visudo
# Add this line:
yourusername ALL=(postgres) NOPASSWD: /usr/bin/psql
```

### 6. Start the server

```bash
export $(cat .env | xargs) && python3 backend/server.py
```

Open your browser at: **http://localhost:8080**

---

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Landing page |
| GET | `/suggest.html` | Suggestion page |
| GET | `/interests.html` | Interests page |
| GET | `/history.html` | History page |
| GET | `/interests?user_id=1` | Fetch user interests |
| POST | `/interests` | Save user interests |
| POST | `/suggest` | Get AI activity suggestion |
| POST | `/surprise` | Get surprise suggestion (no filters) |
| POST | `/log` | Log completed activity |
| GET | `/history?user_id=1` | Fetch activity history |

---

## Prompting Strategy

Groq is prompted with strict constraints to keep suggestions focused:

```
The user has exactly {time} minutes free. They want to do something 
related to: {interests}. Suggest ONE specific activity directly related 
to {interests}. Start with the interest topic directly. Give only the 
activity name and one sentence description. No lists, no markdown, no asterisks.
```

This prevents generic suggestions and forces the model to stay on topic.

---

## Design

**Palette: Candlelit Scholar**
- Background: `#1C1A17` — old wood, candlelight
- Surface: `#2A2620` — aged paper
- Accent: `#C8A97E` — amber gold
- Text: `#EDE8DF` — warm cream
- Muted: `#7A7268` — faded ink

Fonts: Cormorant Garamond (headings) + Inter (body)

---

## Built By

Grismitha — built in one evening as a hackathon project.
