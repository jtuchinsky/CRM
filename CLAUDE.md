# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CRM (Customer Relationship Management) system built with FastAPI. The project is in early development stages with a basic FastAPI application structure.

## Technology Stack

- **Framework**: FastAPI 0.124.0
- **Server**: Uvicorn 0.38.0
- **Python**: 3.12
- **Validation**: Pydantic 2.12.5

## Development Commands

### Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run development server with auto-reload
uvicorn main:app --reload

# Run on specific host/port
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Testing HTTP Endpoints

The project includes `test_main.http` for manual HTTP testing. This file can be used with HTTP client tools in IDEs like PyCharm or VSCode with REST Client extension.

### Package Management

```bash
# Install dependencies
pip install -r requirements.txt  # (if/when requirements.txt is created)

# Add new packages
pip install <package-name>
pip freeze > requirements.txt
```

## Architecture

### Current Structure

- `main.py`: Main FastAPI application entry point with route definitions
- `test_main.http`: HTTP request examples for testing endpoints
- `.venv/`: Python virtual environment (not committed to git)

### Application Entry Point

The FastAPI app is instantiated in `main.py:3` as `app = FastAPI()`. All routes are currently defined in this single file.

### Virtual Environment

The project uses a Python virtual environment located in `.venv/`. A duplicate or backup virtual environment structure exists in `CRM/` directory (appears to be a secondary venv, not application code).

## Current API Endpoints

- `GET /`: Root endpoint returning a hello world message
- `GET /hello/{name}`: Parameterized greeting endpoint

## Development Notes

- The server runs on `http://127.0.0.1:8000` by default
- FastAPI provides automatic interactive API documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- The project follows async/await patterns for route handlers