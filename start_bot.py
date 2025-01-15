import subprocess
import time
import signal
import sys
import logging
import threading

# Configure logging to stdout (captured by systemd)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global references to subprocesses
camera_process = None
nav = None

def start_processes():
    global camera_process, nav
    try:
        # Start CameraFeed_2.py
        camera_process = subprocess.Popen([
            "python3",
            "/home/amjpi/Zakibot/CameraFeed.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logging.info(f"CameraFeed.py started with PID: {camera_process.pid}")

        # Log CameraFeed_2.py output
        def log_camera_output():
            for line in iter(camera_process.stdout.readline, b''):
                logging.info(f"CameraFeed_2.py: {line.decode().strip()}")

        threading.Thread(target=log_camera_output, daemon=True).start()

        time.sleep(2)  # Wait to ensure CameraFeed_2.py starts successfully

        # Start RobotMain.py
        nav = subprocess.Popen([
            "python3",
            "/home/amjpi/Zakibot/nav.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logging.info(f"RobotMain.py started with PID: {nav.pid}")

        # Log RobotMain.py output
        def log_robot_output():
            for line in iter(nav.stdout.readline, b''):
                logging.info(f"RobotMain.py: {line.decode().strip()}")

        threading.Thread(target=log_robot_output, daemon=True).start()

    except Exception as e:
        logging.error(f"Failed to start processes: {e}")
        stop_processes()
        sys.exit(1)

def stop_processes():
    global camera_process, nav
    logging.info("Stopping child processes...")
    if camera_process and camera_process.poll() is None:
        camera_process.terminate()
        try:
            camera_process.wait(timeout=5)
            logging.info("CameraFeed_2.py terminated.")
        except subprocess.TimeoutExpired:
            camera_process.kill()
            logging.warning("CameraFeed_2.py killed after timeout.")

    if nav and nav.poll() is None:
        nav.terminate()
        try:
            nav.wait(timeout=5)
            logging.info("RobotMain.py terminated.")
        except subprocess.TimeoutExpired:
            nav.kill()
            logging.warning("RobotMain.py killed after timeout.")

def handle_signal(signum, frame):
    logging.info(f"Received signal {signum}. Shutting down.")
    stop_processes()
    sys.exit(0)

def monitor_processes():
    global camera_process, nav
    try:
        while True:
            time.sleep(1)
            # Check if any process has terminated unexpectedly
            if camera_process and camera_process.poll() is not None:
                logging.error("CameraFeed_2.py has terminated unexpectedly. Restarting...")
                start_processes()
            if nav and nav.poll() is not None:
                logging.error("RobotMain.py has terminated unexpectedly. Restarting...")
                start_processes()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down.")
        stop_processes()
        sys.exit(0)

def main():
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    start_processes()
    monitor_processes()

if __name__ == "__main__":
    main()
