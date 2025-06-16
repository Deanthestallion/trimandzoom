from flask import Flask, request, send_file, jsonify
import os
import uuid
import subprocess
from zoom_faces import zoom_on_faces
import whisper

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "Video Processing API is running."

@app.route("/process", methods=["POST"])
def process_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files['video']
    input_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.mp4")
    file.save(input_path)

    silent_cut_path = input_path.replace(".mp4", "_cut.mp4")
    zoomed_path = input_path.replace(".mp4", "_zoomed.mp4")
    final_output = os.path.join(PROCESSED_FOLDER, f"{uuid.uuid4()}.mp4")

    try:
        # 1. Remove silent scenes with auto-editor
        subprocess.run([
            "auto-editor", input_path,
            "--video-speed", "99999",
            "--silent-speed", "2.0",
            "--frame-margin", "6",
            "--export", "video",
            "--output", silent_cut_path
        ], check=True)

        # 2. Zoom in on faces
        zoom_on_faces(silent_cut_path, zoomed_path)

        # 3. Generate subtitles with Whisper
        model = whisper.load_model("base")
        result = model.transcribe(zoomed_path)
        subtitle_path = zoomed_path.replace(".mp4", ".srt")
        with open(subtitle_path, "w") as f:
            for i, segment in enumerate(result["segments"]):
                f.write(f"{i+1}\n")
                f.write(f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n")
                f.write(f"{segment['text'].strip()}\n\n")

        # 4. Burn subtitles using ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-i", zoomed_path,
            "-vf", f"subtitles={subtitle_path}",
            "-c:a", "copy", final_output
        ], check=True)

        return jsonify({"download_url": f"/download/{os.path.basename(final_output)}"})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
