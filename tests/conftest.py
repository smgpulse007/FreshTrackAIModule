import sys
import os
from pathlib import Path

# Ensure imports like `from app.main import app` work when running pytest from the workspace root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Ensure current working directory is the service root so relative test paths work
os.chdir(ROOT)
