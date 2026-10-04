from flask import Flask, render_template, request, send_file, abort
import os

app = Flask(__name__)

# Hardcoded tokens you can give to students manually over WhatsApp after they pay
VALID_TOKENS = ["PASS123", "FUTD2026", "EXAM99", "SECURE500"]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view_question', methods=['POST'])
def view_question():
    user_code = request.form.get('access_code', '').strip().upper()
    requested_file = request.form.get('file_name')

    if user_code not in VALID_TOKENS:
        return "<h3>❌ Invalid Access Token! Please verify your payment.</h3><a href='/'>Go Back</a>"

    file_path = f"past_questions/{requested_file}"
    if not os.path.exists(file_path):
        return f"<h3>⚠️ Document Error: File under compilation.</h3><a href='/'>Go Back</a>"

    return render_template('index.html', show_viewer=True, target_file=requested_file)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    file_path = f"past_questions/{filename}"
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/pdf')
    return abort(404)

# Vercel handles serverless routing dynamically via 'app' entry
