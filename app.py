from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from config import Config
from ml_backend_stub import summarize_data, detect_anomalies, generate_visualizations

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    """Panel #1 – Login"""
    if request.method == 'POST':
        # ⬇️ Replace with real auth logic
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            # Success – redirect to dashboard
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Panel #2 – Dashboard / Data assets list"""
    files = [
        f for f in os.listdir(app.config['UPLOAD_FOLDER'])
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))
    ]
    return render_template('dashboard.html', files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Panel #3 – Upload"""
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file selected', 'error')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(dest)
        return redirect(url_for('parsing', filename=filename))
    return render_template('upload.html')

@app.route('/parsing/<filename>')
def parsing(filename):
    """Panel #4 – Parsing progress"""
    # Trigger backend processing synchronously for demo purposes
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    summary = summarize_data(filepath)
    anomalies = detect_anomalies(filepath)
    charts = generate_visualizations(filepath)
    # Persist artifacts so they can be displayed later
    meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}.json')
    with open(meta_path, 'w') as fp:
        fp.write(json.dumps({'summary': summary, 'anomalies': anomalies, 'charts': charts}))
    return redirect(url_for('review', filename=filename))

@app.route('/review/<filename>')
def review(filename):
    """Panel #5 – Review results"""
    meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}.json')
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path))
    else:
        meta = {'summary': 'Processing…', 'anomalies': [], 'charts': []}
    return render_template('review.html', filename=filename, info=meta)

@app.route('/export/<filename>', methods=['GET', 'POST'])
def export(filename):
    """Panel #6 – Export center"""
    # Stub – generate PDF/CSV based on user selections
    if request.method == 'POST':
        # TODO: Build report and return as download / email
        flash('Export initiated – check your inbox!', 'success')
    return render_template('export.html', filename=filename)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
