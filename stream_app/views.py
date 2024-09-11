import cv2
from django.http import StreamingHttpResponse
from django.shortcuts import render
import logging
from deepface import DeepFace

# Set up logging
logger = logging.getLogger(__name__)

# Global variable for video capture state
video_capture = None

def start_video_stream():
    global video_capture
    # Always reinitialize the camera on start
    if video_capture is not None:
        video_capture.release()  # Ensure any previous stream is released
        logger.info("Previous video stream released.")
    
    video_capture = cv2.VideoCapture(0)  # Initialize a fresh webcam capture
    if video_capture.isOpened():
        logger.info("Video stream started.")
    else:
        logger.error("Error: Could not open video stream.")

def stop_video_stream():
    global video_capture
    if video_capture is not None and video_capture.isOpened():
        video_capture.release()
        video_capture = None  # Reset the video capture object
        logger.info("Video stream stopped.")
    else:
        logger.warning("No video stream to stop.")

def generate_frames():
    global video_capture
    if video_capture is None or not video_capture.isOpened():
        logger.error("Error: Video stream is not open.")
        return  # Early exit if the stream is not open

    while True:
        success, image = video_capture.read()
        if not success:
            logger.error("Error: Could not read frame from video stream.")
            break

        # Perform face detection and anti-spoofing using DeepFace
        try:
            face_objs = DeepFace.extract_faces(img_path=image, anti_spoofing=True, enforce_detection=False)
            
            # Draw bounding boxes and labels on the frame
            for face_obj in face_objs:
                facial_area = face_obj["facial_area"]
                x = facial_area.get('x', 0)
                y = facial_area.get('y', 0)
                w = facial_area.get('w', 0)
                h = facial_area.get('h', 0)

                # Check if the face is real or spoofed
                if face_obj["is_real"]:
                    if face_obj["antispoof_score"] >= 0.70:
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(image, 'Real', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                else:
                    if face_obj["antispoof_score"] >= 0.70:
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(image, 'Fake', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        except Exception as e:
            logger.error(f"Error processing DeepFace: {e}")

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', image)
        if not ret:
            logger.error("Error: Could not encode frame.")
            break

        frame = buffer.tobytes()

        # Yield the frame as a response in the multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
    # Check if video capture has been started properly
    global video_capture
    if video_capture is None or not video_capture.isOpened():
        logger.error("Video feed requested, but the stream is not open.")
        return StreamingHttpResponse(status=503)  # Return a 503 Service Unavailable if not streaming

    return StreamingHttpResponse(generate_frames(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    return render(request, 'stream_app/index.html')

def control_stream(request, action):
    if action == "start":
        start_video_stream()
    elif action == "stop":
        stop_video_stream()
    return render(request, 'stream_app/index.html')
