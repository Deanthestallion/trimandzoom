import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
DOMAIN = "https://auto-editor-33k6.onrender.com"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return 'Video Silence + Face Zoom Processor is Running'

@app.route('/process', methods=['POST'])
def process_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = secure_filename(file.filename)
    file_id = uuid.uuid4().hex
    input_path = os.path.join(UPLOAD_FOLDER, f"input_{file_id}.mp4")
    output_path_silence = os.path.join(OUTPUT_FOLDER, f"silence_removed_{file_id}.mp4")
    output_path_final = os.path.join(OUTPUT_FOLDER, f"final_output_{file_id}.mp4")

    file.save(input_path)

    try:
        subprocess.run([
            'auto-editor', input_path,
            '--silent-speed', '99999', '--video-speed', '1',
            '--export', 'ffmpeg', '--output', output_path_silence
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Silence cut failed: {str(e)}'}), 500

    try:
        subprocess.run([
            'python3', 'zoom_faces.py', output_path_silence, output_path_final
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Zooming failed: {str(e)}'}), 500

    return jsonify({
        'message': 'Video processed successfully',
        'download_url': f"{DOMAIN}/download/{os.path.basename(output_path_final)}"
    }), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
