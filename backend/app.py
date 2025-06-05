from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import os

app = Flask(__name__)
CORS(app)

DB = "database.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS survey (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gpa REAL NOT NULL CHECK(gpa >= 4.0 AND gpa <= 12.0),
                first_choice INTEGER NOT NULL,
                major TEXT NOT NULL,
                program TEXT NOT NULL,
                gender TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()


@app.route('/submit', methods=['POST'])
def submit():
    captcha = data.get("captcha", "")

    # Verify with Google
    r = requests.post("https://www.google.com/recaptcha/api/siteverify", data={
        'secret': os.getenv('RECAPTCHA_SECRET_KEY'),
        'response': captcha
    })
    if not r.json().get("success"):
        return "CAPTCHA failed", 400

    data = request.json
    name = data.get('name', '').strip()
    try:
        gpa = float(data.get('gpa'))
    except:
        return 'Invalid GPA', 400
    first_choice = 1 if data.get('first_choice') else 0
    major = data.get('major')
    program = data.get('program')
    gender = data.get('gender')

    if not (name and 2 <= len(name) <= 40):
        return 'Invalid name', 400
    if not (4.0 <= gpa <= 12.0):
        return 'Invalid GPA', 400
    if major not in ("computer", "electrical", "other"):
        return 'Invalid major', 400
    if program not in ("regular", "management", "society"):
        return 'Invalid program', 400
    if gender not in ("male", "female", "other"):
        return 'Invalid gender', 400

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO survey (name, gpa, first_choice, major, program, gender)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, gpa, first_choice, major, program, gender))
        conn.commit()
    return '', 200


@app.route('/data', methods=['GET'])
def data():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT gpa, first_choice, major, program, gender FROM survey')
        rows = c.fetchall()

    # Only Computer Engineering admits
    comp_eng_rows = [r for r in rows if r[2] == "computer"]

    # 1. Cutoff for Computer Eng (lowest GPA of non-free-choice admit)
    non_fc_gpas = [r[0] for r in comp_eng_rows if not r[1]]
    cutoff = min(non_fc_gpas) if non_fc_gpas else None

    # 2. Pie chart categories:
    no_free_choice = 0
    fc_above_cutoff = 0
    fc_below_cutoff = 0

    for gpa, fc, major, program, gender in comp_eng_rows:
        if not fc:
            no_free_choice += 1
        elif cutoff is not None:
            if gpa >= cutoff:
                fc_above_cutoff += 1
            else:
                fc_below_cutoff += 1

    # 3. GPA distribution for computer admits (histogram)
    gpa_bins = [4, 5, 6, 7, 8, 9, 10, 11, 12]
    gpa_counts = [0 for _ in gpa_bins]
    for gpa, fc, major, program, gender in comp_eng_rows:
        for i, b in enumerate(gpa_bins):
            if gpa < b+1:
                gpa_counts[i] += 1
                break

    # 4. Extra: Gender breakdown for Computer admits
    gender_counts = {"male": 0, "female": 0, "other": 0}
    for _, _, _, _, gender in comp_eng_rows:
        if gender in gender_counts:
            gender_counts[gender] += 1

    return jsonify({
        'cutoff': cutoff,
        'pie': {
            'no_free_choice': no_free_choice,
            'fc_above_cutoff': fc_above_cutoff,
            'fc_below_cutoff': fc_below_cutoff,
        },
        'gpa_bins': [f"{b}-{b+1}" for b in gpa_bins],
        'gpa_counts': gpa_counts,
        'gender_counts': gender_counts,
    })


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
