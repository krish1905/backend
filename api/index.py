"""Vercel serverless entry point for FastAPI backend."""
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

# Vercel needs a variable named 'app' or a handler
handler = app

