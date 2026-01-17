# Street Cleanup Backend API

Backend service for managing neighborhood street cleanup activities.  
This service will allow users to discover, join, and verify cleanup activities, and allow admins to manage activity lifecycles.

Built with **FastAPI** and designed to evolve incrementally toward an MVP.

---

## Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn (ASGI server)
- PostgreSQL (planned)
- Alembic (planned)

---

## Project Structure

volunteer_signup/
├── app/
│ ├── main.py # Application entrypoint
│ ├── api/ # Business APIs (to be added)
│ ├── core/ # Configuration, security, logging
│ ├── db/ # Database setup (future)
│ └── tests/
├── requirements.txt
└── README.md

---

## Prerequisites

- Python 3.10 or higher
- pip
- Virtual environment tool (recommended)

---

## Local Setup

### 1. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload
```

The server will start at:
http://127.0.0.1:8000

Health Check

Verify the application is running:
```bash
http://127.0.0.1:8000/health
```

## Local PostgreSQL (Docker)

Start PostgreSQL:
```bash
docker compose up -d
```
PostgreSQL runs on:

Host: localhost

Port: 5432






