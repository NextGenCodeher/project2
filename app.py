import os
import sqlite3
from flask import Flask, request, jsonify, render_template, render_template_string, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
# Ensure the folder exists immediately
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
DB_NAME = "database.db"

# --- DATABASE SETUP ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB immediately when app starts
init_db()

# --- ROUTES ---

@app.route('/')
def index():
    # Make sure you have 'templates/upload.html' created for this to work
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 1. Save to Disk
        file.save(save_path)
        
        # 2. Save info to Database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO uploads (filename) VALUES (?)", (filename,))
            conn.commit()
            conn.close()
        except Exception as e:
            # If DB fails, we still return success if file saved, or you can return 500
            print(f"Database error: {e}") 
            
        return jsonify({'message': f'File {filename} uploaded & saved to DB!'}), 200

# --- VIEW FILES ROUTES (Added per your request) ---

@app.route('/files')
def list_files():
    # This reads the actual folder on the server
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
    except FileNotFoundError:
        files = []
        
    # Simple HTML to show the files list
    html = '''
    <h1>Uploaded Files on Server</h1>
    <ul>
        {% for file in files %}
            <li>
                <a href="/uploads/{{ file }}">{{ file }}</a>
            </li>
        {% else %}
            <li>No files found (Server might have restarted).</li>
        {% endfor %}
    </ul>
    <br>
    <a href="/">Go Back to Upload</a>
    '''
    return render_template_string(html, files=files)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # This allows you to click the link and see/download the file
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)