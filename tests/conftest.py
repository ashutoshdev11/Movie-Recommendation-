import os
import sys

# Ensure repository root is in sys.path for test discovery across unit and integration suites
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
