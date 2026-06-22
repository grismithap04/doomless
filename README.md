# Doomless — Beat the Scroll

Stop doomscrolling. Start doing.

Doomless is a web application that helps you use your free time intentionally. Instead of aimlessly scrolling through social media, get personalized activity suggestions powered by AI.

## Features

- Personalized Suggestions — Get activity recommendations based on your interests and available time
- Quick Actions — One-click access to get suggestions or surprise activities
- Progress Tracking — See your total activities, daily progress, and time saved
- Glassmorphism UI — Modern, elegant, and pleasing visual design
- AI-Powered — Uses Groq API for intelligent activity suggestions
- Data Export — Export your activity history to JSON

## Tech Stack

- HTML/CSS — Frontend UI
- AWK — Backend server
- Python — Alternative backend
- PostgreSQL — Database
- Groq API — AI suggestions
- Git — Version control

## Project Structure

doomless/
├── backend/
│   ├── server.awk        # AWK backend server
│   ├── server.py         # Python backend (alternative)
│   ├── log.awk           # Logging utility
│   └── suggest.awk       # Suggestion engine
├── db/
│   ├── schema.sql        # Database schema
│   ├── functions.sql     # Database functions
│   └── seed.sql          # Seed data
├── frontend/
│   ├── index.html        # Main page
│   ├── style.css         # Styles
│   ├── suggest.html      # Suggestion page
│   └── interests.html    # Interests management
├── sheets/
│   ├── sheets.sh         # Groq API integration
│   └── .env              # API keys (local only)
└── README.md

## Getting Started

### Prerequisites

- Git — For cloning the repository
- AWK — For running the backend server
- PostgreSQL — For the database
- Groq API Key — For AI suggestions

### 1. Clone the Repository

git clone https://github.com/grismithap04/doomless.git
cd doomless

### 2. Set Up the Database

psql -U postgres
CREATE DATABASE doomless;
\i db/schema.sql
\i db/functions.sql
\i db/seed.sql

### 3. Configure Environment

cp .env.example .env
# Edit with your credentials
# Add your Groq API key

### 4. Start the Backend Server

Using AWK:
cd backend
awk -f server.awk

Using Python (alternative):
cd backend
python server.py

### 5. Open the Frontend

Open frontend/index.html in your browser, or use a local server:

python -m http.server 8000

## Setting Up Groq API

### 1. Get Your API Key

1. Go to console.groq.com
2. Sign up or log in
3. Go to API Keys
4. Click Create API Key
5. Copy the key (starts with gsk_)

### 2. Configure the Sheets Script

cd sheets
./sheets.sh setup
# Enter your Groq API key when prompted

### 3. Test the Connection

./sheets.sh test
# Should show: Groq API connection successful!

## Using the Sheets Script

The sheets.sh script manages data export and API integration:

- ./sheets.sh help — Show all commands
- ./sheets.sh setup — Configure Groq API key
- ./sheets.sh test — Test API connection
- ./sheets.sh export — Export activities to JSON
- ./sheets.sh config — Show current settings

Example usage:
cd sheets
./sheets.sh export  # Exports to data/export_*.json

## How It Works

1. Set Your Time — Tell the app how many minutes you have free
2. Pick Interests — Choose what you enjoy (running, music, baking, etc.)
3. Get a Suggestion — Groq AI recommends a focused activity
4. Log It — Mark it done and track your progress

## Browser Support

- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

## Contributing

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Team

- Grishmitha — Project Owner
- Kaanasreek — Contributor
- Pondharani — Contributor
- Sowbaranika — Contributor

## Acknowledgments

- Groq — For AI API
- Font Awesome — For icons
- Google Fonts — For typography

## Troubleshooting

### Backend won't start

Check if port 8080 is in use:
netstat -ano | findstr :8080

Kill the process using the port:
Windows: taskkill /PID <PID> /F
Linux: kill -9 <PID>

### API connection fails

Test Groq API key:
cd sheets
./sheets.sh test

If fails, recreate the key at console.groq.com

### Database connection issues

Check PostgreSQL status:
sudo systemctl status postgresql

Restart PostgreSQL:
sudo systemctl restart postgresql

---

Made by the Doomless Team
