from picamera2 import Picamera2
from flask import Flask, Response, render_template_string
import cv2
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Picamera2
picam2 = Picamera2()
# Configure the camera with desired settings
config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()
logger.info("Camera initialized and started.")

# Shared variable to store the latest frame
latest_frame = None
frame_lock = threading.Lock()

def capture_frames():
    global latest_frame
    while True:
        try:
            # Capture frame from camera
            frame = picam2.capture_array()
            if frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    with frame_lock:
                        latest_frame = buffer.tobytes()
                    logger.debug("Captured and encoded a frame.")
                else:
                    logger.warning("Failed to encode frame.")
            else:
                logger.warning("Captured frame is None.")
        except Exception as e:
            logger.error(f"Exception in capture_frames: {e}")
            break
        # Control frame rate (adjust as needed)
        time.sleep(0.03)  # Approximately 30 FPS

# Start the frame capture thread
capture_thread = threading.Thread(target=capture_frames, daemon=True)
capture_thread.start()
logger.info("Started frame capture thread.")

def generate_mjpeg_stream():
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame

        try:
            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except GeneratorExit:
            logger.info("Client disconnected, stopping stream.")
            break
        except Exception as e:
            logger.error(f"Exception in generate_mjpeg_stream: {e}")
            break

@app.route('/video_feed')
def video_feed():
    """Video streaming route using MJPEG."""
    logger.info("Client connected to /video_feed.")
    response = Response(
        generate_mjpeg_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
    # Prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    """Home page with embedded image."""
    logger.info("Client connected to / (index).")
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Live Camera Feed</title>
    </head>
    <body>
        <h1>Live Camera Feed</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    logger.info("Starting Flask app.")
    # Note: When using Gunicorn, you don't run the app here.
    # Instead, you use the Gunicorn command to run the app.
    app.run(host="0.0.0.0", port=5000, threaded=True)
    # pass
