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

    suggestion = call_gemini(time_val, interests)
    return jsonify({"suggestion": suggestion})

@app.route('/surprise', methods=['POST'])
def surprise():
    time_val = request.form.get('time', '30')
    suggestion = call_gemini(time_val, '')
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
            urllib.request.urlopen(req)
            print("SHEETS: logged successfully")
    except Exception as e:
        print("SHEETS ERROR:", e)

    return jsonify({"status": "ok"})

def call_gemini(time_val, interests):
    api_key = os.environ.get('GROQ_API_KEY', '')
    if interests:
        prompt = f"The user has exactly {time_val} minutes free. They want to do something related to: {interests}. Suggest ONE specific activity directly related to {interests}. Start with the interest topic directly. No shadow puppets, no unrelated activities. Give only the activity name and one sentence description. No lists, no markdown, no asterisks."
    else:
        prompt = f"Suggest one surprising creative activity for someone with {time_val} minutes free. Give only the activity name and one sentence. No lists, no markdown."

    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "curl/7.68.0"
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        return data['choices'][0]['message']['content']
    except Exception as e:
        print("GROQ ERROR:", e)
        return "Take a 5-minute walk and breathe some fresh air."


if __name__ == '__main__':
    print("DOOMLESS server starting on port 8080")
    app.run(port=8080, debug=False)
