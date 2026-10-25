"""tests/conftest.py
Pytest configuration for DAR Fake Job Detector.
Adds project root to sys.path so modules like ml and app can be imported directly.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
