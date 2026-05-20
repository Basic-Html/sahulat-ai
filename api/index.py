import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.staticfiles import StaticFiles
from backend.main import app

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

try:
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
except:
    pass

handler = app