"""
WSGI entry point para Gunicorn/producción
Uso: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import app

if __name__ == "__main__":
    app.run()
