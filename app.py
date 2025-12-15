import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Database File Name
DB_NAME = "database.db"

# --- DATABASE SETUP ---
def init_db():
    """Creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
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

def get_db_connection():
    """Helper to get a connection to the DB."""
    conn = sqlite3.connect(DB_NAME)
    # This line makes columns accessible by name (row['filename'])
    conn.row_factory = sqlite3.Row 
    return conn

# --- ROUTES ---

@app.route('/')
def index():
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
        
        # 1. Save physical file
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        # 2. Save info to SQLite Database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO uploads (filename) VALUES (?)", (filename,))
            conn.commit()
            conn.close()
            print(f"✅ Saved {filename} to database.")
        except Exception as e:
            print(f"❌ DB Error: {e}")
            return jsonify({'error': 'Database write failed'}), 500
        
        return jsonify({'message': f'File {filename} uploaded & saved to DB!'}), 200

# New Route: View all uploads (Optional, for testing)
@app.route('/history')
def history():
    conn = get_db_connection()
    uploads = conn.execute('SELECT * FROM uploads ORDER BY id DESC').fetchall()
    conn.close()
    # Simple list view of what is in the DB
    return jsonify([dict(row) for row in uploads])

if __name__ == '__main__':
    # Initialize DB before starting server
    init_db()
    app.run(debug=True)