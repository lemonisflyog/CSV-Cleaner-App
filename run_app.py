import os
import subprocess
import webbrowser
import sys
import time

APP_FILE = "csv_cleaner_app.py"
LOCK_FILE = ".browser_opened"
CONFIG_FILE = os.path.join(".streamlit", "config.toml")

try:
    # Launch Streamlit app with explicit config
    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", APP_FILE,
            "--server.headless", "true",
            "--config", CONFIG_FILE
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give server a moment to start
    time.sleep(2)

    # Open browser only once using a lock file
    if not os.path.exists(LOCK_FILE):
        webbrowser.open("http://localhost:8501")
        with open(LOCK_FILE, "w") as f:
            f.write("opened")

    # Keep running until Streamlit exits
    process.wait()

except Exception as e:
    print(f"Error: {e}")
    input("Press Enter to close...")

finally:
    # Clean up the lock file when process exits
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
