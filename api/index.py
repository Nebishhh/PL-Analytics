"""Vercel entrypoint. Deployment shim only: imports the unchanged app."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from backend.app import app  # noqa: E402,F401
