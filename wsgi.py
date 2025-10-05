"""WSGI entry point for gunicorn"""
import sys
import os

print(f"[WSGI] Loading WSGI module", flush=True)
print(f"[WSGI] Python path: {sys.path}", flush=True)
print(f"[WSGI] Working directory: {os.getcwd()}", flush=True)

try:
    from app import app
    print(f"[WSGI] Successfully imported app: {app}", flush=True)
except Exception as e:
    print(f"[WSGI] Failed to import app: {e}", flush=True)
    import traceback
    traceback.print_exc()
    raise

print(f"[WSGI] WSGI module loaded successfully", flush=True)
