import sys
import os
import state
import log_utils
from ui_main import launch_main_ui

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        # Running as packaged exe → use folder where the exe resides
        state.BASE_DIR = os.path.dirname(sys.executable)

    else:
        state.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create logs folder + file before UI loads
    log_utils.setup_logging()
    launch_main_ui()
