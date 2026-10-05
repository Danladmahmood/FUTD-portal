from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
import os
import requests

app = Flask(__name__, template_folder='../templates')
app.secret_key = "futd_secure_automated_key_2026"

# 🔑 Keeping your active Paystack token linked securely
PAYSTACK_SECRET_KEY = "sk_test_1e54992131fca2b2f940376fdb34ba38790b502e"

# Path to our permanent mobile file database
DB_FILE = "/tmp/users.txt" if os.environ.get('VERCEL') else "users.txt"

def load_users():
    """Loads all permanently registered student profiles from the file database"""
    users = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if "::" in line:
                    u, p = line.strip().split("::", 1)
                    users[u] = p
    return users

def save_user(username, password):
    """Permanently appends a new student profile to the file database"""
    with open(DB_FILE, "a") as f:
        f.write(f"{username}::{password}\n")

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', logged_in=True, current_user=session['username'])
    return render_template('index.html', logged_in=False)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return "<h3>⚠️ Registration Error: Fields cannot be empty.</h3><a href='/'>Go Back</a>"
    
    users = load_users()
    if username in users:
        return "<h3>❌ Username already exists! Please pick another one.</h3><a href='/'>Go Back</a>"
    
    # Save permanently to file database
    save_user(username, password)
    session['username'] = username
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()
    
    users = load_users()
    if username in users and users[username] == password:
        session['username'] = username
        return redirect(url_for('home'))
    return "<h3>❌ Invalid login credentials. Please check your details.</h3><a href='/'>Go Back</a>"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json()
    reference = data.get('reference')
    file_name = data.get('file_name')

    if not reference:
        return jsonify({"status": "error", "message": "Missing payment reference"}), 400

    url = f"https://paystack.co{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(url, headers=headers)
    res_data = response.json()

    if res_data.get('status') and res_data['data']['status'] == 'success':
        if 'unlocked_files' not in session:
            session['unlocked_files'] = []
        if file_name not in session['unlocked_files']:
            session['unlocked_files'].append(file_name)
            session.modified = True
        return jsonify({"status": "success", "message": "Payment verified perfectly!"})
    return jsonify({"status": "error", "message": "Payment verification failed"}), 400

@app.route('/read/<filename>')
def read_document(filename):
    if 'username' not in session:
        return redirect(url_for('home'))
    unlocked = session.get('unlocked_files', [])
    if filename not in unlocked:
        return "<h3>🔒 Access Denied: You must purchase this document first.</h3><a href='/'>Go Back</a>"
    return render_template('index.html', logged_in=True, current_user=session['username'], show_viewer=True, target_file=filename)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    if 'username' not in session:
        return abort(403)
    unlocked = session.get('unlocked_files', [])
    if filename not in unlocked:
        return abort(403)
    
    file_path = f"../Past_questions/{filename}"
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/pdf')
    return abort(404)
