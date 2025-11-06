import os
from datetime import datetime
import tkinter as tk
import state

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MAX_LOG_SIZE_MB = 10        # roll over threshold
MAX_LOG_SIZE_BYTES = MAX_LOG_SIZE_MB * 1024 * 1024
MAX_LOG_BACKUPS = 5         # retain only last 5 rolled logs


def setup_logging():
    """Create logs folder and prepare initial log file."""
    state.LOG_DIR = os.path.join(state.BASE_DIR, "logs")
    os.makedirs(state.LOG_DIR, exist_ok=True)

    if not hasattr(state, "LOG_FILE_NAME"):
        state.LOG_FILE_NAME = "fts_log.txt"

    state.LOG_FILE = os.path.join(state.LOG_DIR, state.LOG_FILE_NAME)
    print(f"✅ Logging initialized at: {state.LOG_FILE}")


def _cleanup_old_logs():
    """Keep only the latest N rolled logs."""
    if not os.path.exists(state.LOG_DIR):
        return

    base = os.path.splitext(state.LOG_FILE_NAME)[0]
    rolled_files = sorted(
        [
            os.path.join(state.LOG_DIR, f)
            for f in os.listdir(state.LOG_DIR)
            if f.startswith(base + "_") and f.endswith(".txt")
        ],
        key=os.path.getmtime,
        reverse=True
    )

    if len(rolled_files) > MAX_LOG_BACKUPS:
        for old_file in rolled_files[MAX_LOG_BACKUPS:]:
            try:
                os.remove(old_file)
                print(f"🗑️ Removed old log file: {os.path.basename(old_file)}")
            except Exception as e:
                print(f"⚠️ Failed to delete old log {old_file}: {e}")


def _roll_log_if_needed():
    """Check log file size and roll over if > MAX_LOG_SIZE_MB."""
    if not os.path.exists(state.LOG_FILE):
        return

    file_size = os.path.getsize(state.LOG_FILE)
    if file_size >= MAX_LOG_SIZE_BYTES:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rolled_file = os.path.join(
            state.LOG_DIR,
            f"{os.path.splitext(state.LOG_FILE_NAME)[0]}_{timestamp}.txt"
        )

        try:
            os.rename(state.LOG_FILE, rolled_file)
            print(f"🔁 Rolled log file to: {rolled_file}")
            _cleanup_old_logs()  # remove older backups
        except Exception as e:
            print(f"⚠️ Log rollover failed: {e}")


def log_message(message):
    """Write a message to the log file and optionally the Tkinter log window."""
    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    log_entry = f"{timestamp} - {message}"

    # Mask sensitive info
    if "Client Secret:" in message:
        message = "Client Secret: <encrypted>"
        log_entry = f"{timestamp} - {message}"

    # Color-coding for log window
    if "error" in message.lower():
        color = "red"
    elif "success" in message.lower():
        color = "green"
    else:
        color = "#00008B"

    # Write to Tkinter log window if present
    if getattr(state, "log_window", None):
        state.log_window.tag_config(color, foreground=color)
        state.log_window.insert(tk.END, f"{log_entry}\n", color)
        state.log_window.yview(tk.END)

    # Ensure log setup
    if not hasattr(state, "LOG_FILE"):
        setup_logging()

    # Roll if needed and then write
    _roll_log_if_needed()
    try:
        with open(state.LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry + "\n")
    except Exception as e:
        print(f"⚠️ Failed to write log: {e}")
