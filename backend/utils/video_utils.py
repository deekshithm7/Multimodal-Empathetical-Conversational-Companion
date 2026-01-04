import cv2

def extract_frames(video_path, step=10):
    cap = cv2.VideoCapture(video_path)
    frames = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if idx % step == 0:
            frame = cv2.resize(frame, (224, 224))
            frames.append(frame)

        idx += 1

    cap.release()
    return frames
