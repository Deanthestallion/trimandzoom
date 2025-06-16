from flask import Flask, request, jsonify
import os
import uuid
from moviepy.editor import VideoFileClip
import subprocess

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return "Trim & Zoom API is running."

@app.route('/process', methods=['POST'])
def process_video():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No video uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save uploaded video
        filename = str(uuid.uuid4()) + ".mp4"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Step 1: Remove silence using auto-editor
        trimmed_path = os.path.join(PROCESSED_FOLDER, f"trimmed_{filename}")
        result = subprocess.run([
            "auto-editor", filepath,
            "--silent-speed", "99999",
            "--video-speed", "1",
            "--frame-margin", "6",
            "--export", "video",
            "-o", trimmed_path
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({'error': 'Auto-editor failed', 'details': result.stderr}), 500

        # Step 2: Zoom on faces using OpenCV + MoviePy
        zoomed_path = os.path.join(PROCESSED_FOLDER, f"zoomed_{filename}")
        subprocess.run(["python", "zoom_faces.py", trimmed_path, zoomed_path], check=True)

        return jsonify({'message': 'Video processed successfully', 'url': zoomed_path})

    except Exception as e:
        import traceback
        return jsonify({'error': 'Something went wrong', 'exception': str(e), 'trace': traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
