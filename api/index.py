import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.main import app
from fastapi.staticfiles import StaticFiles

# Mount frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

handler = app