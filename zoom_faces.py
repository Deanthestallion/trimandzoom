import cv2
import os
import shutil

def zoom_on_faces(input_path, output_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        print("Error opening video")
        return False

    has_face = False
    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = face_cascade.detectMultiScale(frame, 1.3, 5)
        if len(faces) > 0:
            has_face = True
            (x, y, w, h) = faces[0]
            margin = 30
            x = max(x - margin, 0)
            y = max(y - margin, 0)
            w = min(w + 2*margin, width - x)
            h = min(h + 2*margin, height - y)

            cropped = frame[y:y+h, x:x+w]
            zoomed = cv2.resize(cropped, (width, height))
            frames.append(zoomed)
        else:
            frames.append(frame)

    cap.release()

    if not has_face:
        print("No faces found. Skipping zoom.")
        shutil.copy(input_path, output_path)
        return True

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for f in frames:
        out.write(f)
    out.release()
    return True
