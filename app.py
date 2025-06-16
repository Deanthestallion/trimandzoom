import os
import time
from uuid import uuid4
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return 'Video Silence Remover API is running.'


@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, f"{uuid4().hex}_{filename}")
    file.save(input_path)

    # Generate output filename
    output_filename = f"silence_removed_{uuid4().hex}.mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    # Run auto-editor (requires auto-editor to be installed and in PATH)
    try:
        cmd = [
            'auto-editor',
            input_path,
            '--silent-threshold', '0.03',
            '--margin', '0.2',
            '--frame-margin', '6',
            '--video-speed', '1',
            '--silent-speed', '99999',
            '--export', 'ffmpeg',
            '--output', output_path
        ]
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Processing failed', 'details': str(e)}), 500

    # Wait until file is fully written
    timeout = 120  # seconds
    start_time = time.time()
    while not os.path.exists(output_path):
        if time.time() - start_time > timeout:
            return jsonify({'error': 'Timed out waiting for output file'}), 500
        time.sleep(1)

    # Return the download link
    return jsonify({
        'message': 'Video processed successfully',
        'download_url': f"{request.host_url}download/{output_filename}"
    })


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not ready or not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
