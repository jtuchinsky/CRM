"""
CRM Application Entry Point

Run with: uvicorn main:app --reload
Or with UV: uv run uvicorn main:app --reload
"""

from app import app

# The app instance is imported from app package
# This allows running: uvicorn main:app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
