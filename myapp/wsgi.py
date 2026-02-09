"""
WSGI entrypoint for production servers (e.g. Gunicorn).
"""

from myapp import create_app

app = create_app()

if __name__ == "__main__":
    # Allows running via: python wsgi.py (dev / debugging only)
    app.run()
