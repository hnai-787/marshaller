import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

REPO_ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_DIR = REPO_ROOT / "topology"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
