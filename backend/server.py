from flask import Flask, request, redirect, jsonify
import subprocess, os, json, urllib.request

app = Flask(__name__, static_folder='../frontend')

@app.route('/')
@app.route('/index.html')
def index():
    return app.send_static_file('index.html')

@app.route('/style.css')
def css():
    return app.send_static_file('style.css')

@app.route('/interests.html')
def interests_page():
    return app.send_static_file('interests.html')

@app.route('/suggest.html')
def suggest_page():
    return app.send_static_file('suggest.html')

@app.route('/history.html')
def history_page():
    return app.send_static_file('history.html')

@app.route('/interests', methods=['GET'])
def get_interests():
    user_id = request.args.get('user_id', '1')
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'doomless', '-t', '-c',
         f'SELECT interest FROM interests WHERE user_id={user_id};'],
        capture_output=True, text=True)
    interests = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    return jsonify({"interests": interests})

@app.route('/interests', methods=['POST'])
def save_interests():
    user_id = request.form.get('user_id', '1')
    interests = request.form.getlist('interests')
    subprocess.run(['sudo', '-u', 'postgres', 'psql', '-d', 'doomless', '-c',
                    f'DELETE FROM interests WHERE user_id={user_id};'],
                   capture_output=True)
    for interest in interests:
        subprocess.run(['sudo', '-u', 'postgres', 'psql', '-d', 'doomless', '-c',
                        f"INSERT INTO interests (user_id, interest) VALUES ({user_id}, '{interest}');"],
                       capture_output=True)
    return jsonify({"status": "ok"})

@app.route('/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id', '1')
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'doomless', '-t', '-A', '-F', '|', '-c',
         f'SELECT activity, time_spent, logged_at FROM activity_log WHERE user_id={user_id} ORDER BY logged_at DESC;'],
        capture_output=True, text=True)
    items = []
    for line in result.stdout.splitlines():
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                items.append({
                    "suggestion": parts[0],
                    "time_available": int(parts[1]) if parts[1].isdigit() else 0,
                    "logged_at": parts[2],
                    "interests_used": []
                })
    return jsonify({"history": items})


def get_recent_titles(user_id, limit=3):
    """Pull the last `limit` activity titles for this user from activity_log,
    so we can tell the model what NOT to repeat."""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-d', 'doomless', '-t', '-A', '-c',
             f'SELECT activity FROM activity_log WHERE user_id={user_id} '
             f'ORDER BY logged_at DESC LIMIT {limit};'],
            capture_output=True, text=True, timeout=5)
        titles = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        return titles
    except Exception as e:
        print("HISTORY FETCH ERROR:", e)
        return []


@app.route('/suggest', methods=['POST'])
def suggest():
    time_val = request.form.get('time', '30')
    user_id  = request.form.get('user_id', '1')
    surprise = request.form.get('surprise', '0')

    if surprise == '1':
        interests = ''
    else:
        interests_list = request.form.getlist('interests')
        interests = ', '.join(interests_list) if interests_list else ''

    recent_titles = get_recent_titles(user_id)
    suggestion = call_gemini(time_val, interests, recent_titles)
    return jsonify({"suggestion": suggestion})

@app.route('/surprise', methods=['POST'])
def surprise():
    time_val = request.form.get('time', '30')
    user_id  = request.form.get('user_id', '1')
    recent_titles = get_recent_titles(user_id)
    suggestion = call_gemini(time_val, '', recent_titles)
    return jsonify({"suggestion": suggestion})

@app.route('/log', methods=['POST'])
def log():
    user_id    = request.form.get('user_id', '1')
    activity   = request.form.get('activity', '').replace("'", "''")
    time_spent = request.form.get('time_spent', '0')

    # Save to Postgres
    subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'doomless', '-c',
         f"INSERT INTO activity_log (user_id, activity, time_spent) VALUES ({user_id}, '{activity}', {time_spent});"],
        capture_output=True)

    # Save to Google Sheets
    try:
        sheets_url = os.environ.get('SHEETS_URL', '')
        if sheets_url:
            from datetime import datetime
            payload = json.dumps({
                "user_id": user_id,
                "activity": activity,
                "time_spent": time_spent,
                "logged_at": datetime.now().isoformat()
            }).encode()
            req = urllib.request.Request(
                sheets_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "curl/7.68.0"
                }
            )
            urllib.request.urlopen(req, timeout=10)
            print("SHEETS: logged successfully")
    except Exception as e:
        print("SHEETS ERROR:", e)

    return jsonify({"status": "ok"})


def trim_to_word_limit(text, max_words):
    """Safety-net word trim, in case the model drifts past the requested limit."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]).rstrip('.,;:') + '...'


def call_gemini(time_val, interests, recent_titles=None):
    api_key = os.environ.get('GROQ_API_KEY', '')
    recent_titles = recent_titles or []

    system_prompt = """You are a recommendation engine for an anti-doomscrolling app. Return ONLY valid JSON. No markdown, no code fences, no explanation, no preamble — the response must start with { and end with }.

Rules:
- Give exactly ONE recommendation.
- Never suggest social media, short-video apps, reels, feeds, or scrolling platforms.
- Keep recommendation under 50 words. Keep title under 8 words.

TIME SCALING (CRITICAL):
- 1-10 min: Single self-contained micro-action (e.g., "write 5 things you're grateful for", "do 20 jumping jacks")
- 11-30 min: Sequential activity with 2-3 phases (e.g., "warmup stretch, main activity, cooldown reflection")
- 31-60 min: Project-based with clear beginning-middle-end (e.g., "research, sketch, finalize")
- 60+ min: Immersive experience with natural stopping points (e.g., "watch tutorial, practice, create final piece, reflect")
- duration_minutes in your output MUST equal the time_available given in the user prompt.
- If time_available is 1-2 minutes, suggest the smallest meaningful action possible (e.g., "take 10 slow breaths"). Never refuse or return an error for very short or unusual durations.

ACTIVITY MUST BE:
- ENGAGED: Either physically/mentally active, OR intentionally mindful (e.g., really listening to a full album with eyes closed, deliberately watching one chosen tutorial, sitting with a specific intention). Idle/passive default behavior like background scrolling or half-watching something is NOT allowed, but focused, single-purpose listening/watching IS allowed.
- SOLO: No other human needed (tutorials/recordings are okay as guides).
- SELF-DIRECTED: No classes, workshops, events, or group activities.
- DOABLE NOW: With what you have at home (phone, paper, basic kitchen items, space to move).

INTEREST RELEVANCE (CRITICAL):
- If the user provided interests, the recommendation MUST directly use or reference at least one stated interest by name or clear equivalent (e.g., if "guitar" is an interest, the activity must involve a guitar/music-making action, not a generic walk or unrelated task).
- Do not substitute a generic wellness activity (walking, breathing, journaling) when a specific interest is provided, unless no other interpretation is reasonably possible for the given time.

REPEAT AVOIDANCE:
- You will be given a list of RECENT_SUGGESTIONS (may be empty).
- Never repeat the same activity, title, or near-identical variation of anything in RECENT_SUGGESTIONS.
- If interests are limited and force overlap, choose a meaningfully different angle, format, or sub-activity within that interest.

SURPRISE ME MODE:
- If user provided no interests, suggest something completely novel and accessible (e.g., "origami", "micro-journaling", "shadow drawing", "blind contour drawing", "one-page zine making").
- Apply the same REPEAT AVOIDANCE rule against RECENT_SUGGESTIONS — do not suggest anything already listed there.

ENVIRONMENT ASSUMPTIONS:
- You are at home, indoors.
- You have: phone/computer, internet, paper + pen, basic kitchen items, floor space.
- If an interest requires special equipment (e.g., photography), assume a basic version (phone camera) is available, not professional gear.

CATEGORY SELECTION (choose exactly one, using this logic):
- "creative": making/producing something (drawing, writing, crafting, music-making)
- "physical": bodily movement or exercise
- "mental": puzzles, learning, strategic/analytical thinking
- "reflective": journaling, mindfulness, quiet intentional listening/sitting
- "practical": tidying, organizing, small real-world tasks
- "adventurous": trying something new/unfamiliar, especially in SURPRISE ME mode
- If an activity could fit multiple categories, choose based on its PRIMARY action (e.g., "sketch while listening to music" -> creative, not reflective).

LANGUAGE:
- Use neutral, descriptive language.
- NO: "should", "ought to", "it's important", "you need to".
- YES: "Try", "Practice", "Explore", "Experiment with".
- Do not give medical or mental health advice. Do not moralize.

Output format:
{"title": "string", "recommendation": "string", "duration_minutes": number, "category": "string"}"""

    recent_str = json.dumps(recent_titles) if recent_titles else '[]'
    user_prompt = (
        f"time_available: {time_val} minutes, "
        f"interests: {interests if interests else 'none'}, "
        f"RECENT_SUGGESTIONS: {recent_str}"
    )

    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        raw = data['choices'][0]['message']['content']
        parsed = json.loads(raw)

        title = parsed.get('title', '').strip()
        recommendation = parsed.get('recommendation', '').strip()

        # Safety-net trims in case the model drifts past requested limits
        title = trim_to_word_limit(title, 8)
        recommendation = trim_to_word_limit(recommendation, 50)

        try:
            duration = int(parsed.get('duration_minutes', time_val))
        except (ValueError, TypeError):
            duration = int(time_val) if str(time_val).isdigit() else 30

        return json.dumps({
            "title": title,
            "recommendation": recommendation,
            "duration_minutes": duration,
            "category": parsed.get('category', '')
        })
    except urllib.error.HTTPError as e:
        print("GROQ ERROR:", e.code, e.read().decode())
        return json.dumps({
            "title": "Quick Reset",
            "recommendation": "Take a 5-minute walk and breathe some fresh air.",
            "duration_minutes": int(time_val) if str(time_val).isdigit() else 5,
            "category": "physical"
        })
    except Exception as e:
        print("GROQ ERROR:", e)
        return json.dumps({
            "title": "Quick Reset",
            "recommendation": "Take a 5-minute walk and breathe some fresh air.",
            "duration_minutes": int(time_val) if str(time_val).isdigit() else 5,
            "category": "physical"
        })


if __name__ == '__main__':
    print("DOOMLESS server starting on port 8080")
    app.run(port=8080, debug=False)