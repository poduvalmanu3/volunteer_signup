# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Backend service for managing neighborhood street cleanup activities ("Cleanup Crew"). Built with FastAPI and PostgreSQL, designed to evolve incrementally toward an MVP. Users can discover, join, and verify cleanup activities; admins can manage activity lifecycles.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 15 (containerized)
- **ORM**: SQLAlchemy 2.0 with declarative models
- **Migrations**: Alembic
- **Authentication**: JWT tokens with passlib[bcrypt] for password hashing, python-jose for token encoding
- **Server**: Uvicorn (ASGI)

## Development Commands

### Initial Setup

1. Create virtual environment and activate:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and configure (or use defaults):
   ```bash
   cp .env.example .env
   ```

4. Start PostgreSQL via Docker:
   ```bash
   docker compose up -d
   ```

### Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`

Health check endpoint: `http://127.0.0.1:8000/health`

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Downgrade one migration:
```bash
alembic downgrade -1
```

View migration history:
```bash
alembic history
```

### Docker Commands

Start database:
```bash
docker compose up -d
```

Stop database:
```bash
docker compose down
```

View logs:
```bash
docker compose logs -f db
```

## Architecture

### Application Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization, router registration, startup events
│   ├── api/
│   │   ├── auth.py          # Authentication endpoints (signup, login)
│   │   └── v1/api.py        # API v1 router (currently empty placeholder)
│   ├── core/
│   │   ├── config.py        # Pydantic settings, environment variables
│   │   ├── security.py      # JWT creation, password hashing/verification
│   │   └── deps.py          # FastAPI dependencies
│   ├── db/
│   │   ├── base.py          # SQLAlchemy declarative base
│   │   ├── engine.py        # Database engine configuration
│   │   ├── session.py       # SessionLocal factory
│   │   ├── deps.py          # Database session dependency (get_db)
│   │   └── check.py         # Database connection health check
│   ├── models/              # SQLAlchemy ORM models
│   │   └── user.py          # User model with UUID primary key
│   └── schemas/             # Pydantic schemas for request/response validation
│       ├── user.py          # UserCreate, UserLogin schemas
│       └── token.py         # Token schema
├── alembic/                 # Database migrations
│   ├── env.py               # Alembic environment configuration
│   └── versions/            # Migration files
├── alembic.ini              # Alembic configuration
└── requirements.txt
```

### Key Architectural Patterns

**Database Connection Management**:
- Engine created in `app/db/engine.py` using settings from `app/core/config.py`
- `SessionLocal` factory in `app/db/session.py` for creating database sessions
- `get_db()` dependency in `app/db/deps.py` yields sessions with automatic cleanup
- Database URL configured via environment variable `DATABASE_URL`

**Configuration Management**:
- Pydantic `BaseSettings` in `app/core/config.py` loads from `.env` file
- Required environment variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `DATABASE_URL`
- Single `settings` instance imported throughout the app

**Authentication Flow**:
- JWT-based authentication with tokens stored in `app/core/security.py`
- Password hashing uses bcrypt via passlib
- Tokens include user ID (`sub`), role, and expiration (`exp`)
- Default token expiration: 60 minutes
- **Security Note**: SECRET_KEY is hardcoded as "CHANGE_ME_IN_PROD" - must be moved to environment variables for production

**Router Organization**:
- Auth endpoints mounted directly: `app.include_router(auth_router)` → routes at `/auth/*`
- API v1 router mounted with prefix: `app.include_router(api_router, prefix="/api/v1")` → routes at `/api/v1/*`
- Auth router in `app/api/auth.py` handles signup and login
- API v1 router in `app/api/v1/api.py` is currently a placeholder for future feature endpoints

**Model Design**:
- UUID primary keys (not auto-incrementing integers) for all models
- `created_at` timestamps with server-side defaults using `func.now()`
- Enum-like fields (e.g., user roles) enforced with database `CheckConstraint`
- User model supports 'USER' and 'ADMIN' roles

**Alembic Integration**:
- `alembic/env.py` imports all models via `import app.models` to ensure autogenerate detects changes
- `target_metadata` set to `Base.metadata` for model tracking
- Database URL dynamically set from settings: `config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)`
- Models must be imported in `app/db/base.py` or `app/models/__init__.py` for Alembic to detect them

### Database Schema

**Users Table**:
- `id`: UUID (primary key)
- `name`: String(255), not null
- `email`: String(255), not null, unique
- `role`: String(20), not null, constrained to 'USER' or 'ADMIN'
- `password_hash`: String(255), not null
- `created_at`: DateTime with timezone, server default now()

## Development Workflow

### Adding a New Model

1. Create model class in `app/models/` inheriting from `Base`
2. Import model in `app/models/__init__.py` or ensure it's imported in `alembic/env.py`
3. Generate migration: `alembic revision --autogenerate -m "add [model_name] table"`
4. Review the generated migration file in `alembic/versions/`
5. Apply migration: `alembic upgrade head`

### Adding New API Endpoints

1. Create router file in `app/api/` or `app/api/v1/`
2. Define endpoints using FastAPI decorators
3. Use `Depends(get_db)` for database access
4. Create Pydantic schemas in `app/schemas/` for request/response validation
5. Register router in `app/main.py` or `app/api/v1/api.py`

### Environment Variables

Required in `.env` (see `.env.example`):
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_PORT`: Database port (default 5432)
- `DATABASE_URL`: Full connection string (e.g., `postgresql://user:password@localhost:5432/dbname`)

## Current State

**Implemented**:
- Basic FastAPI application with health check
- User authentication (signup, login) with JWT tokens
- PostgreSQL database with Docker
- Alembic migrations
- User model with role-based access (USER, ADMIN)

**Pending**:
- Move SECRET_KEY to environment variables
- Implement protected endpoints with JWT verification middleware
- Add refresh token support
- Implement cleanup activity models and endpoints
- Add role-based authorization decorators
- Add API documentation and examples
