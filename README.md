# Cleanup Crew

Community-driven neighborhood street cleanup platform. Users can discover, join, and verify cleanup activities. Admins manage activity lifecycles.

---

## Monorepo Structure

```
volunteer_signup/
├── backend/          # FastAPI REST API
└── frontend/
    └── cleanup-crew/ # Next.js web app
```

---

## Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Backend   | Python 3.10+, FastAPI, SQLAlchemy, Alembic      |
| Database  | PostgreSQL (via Docker)                         |
| Auth      | JWT (python-jose), bcrypt (passlib)             |
| Frontend  | Next.js 16, React 19, TypeScript, CSS Modules   |
| Forms     | react-hook-form                                 |

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

---

## Backend Setup

### 1. Create and activate a virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql://cleanup_user:cleanup_password@localhost:5432/cleanup_db
SECRET_KEY=your-secret-key-here
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 4. Start PostgreSQL

```bash
docker compose up -d
```

### 5. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 6. Start the API server

```bash
uvicorn app.main:app --reload
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

## Frontend Setup

### 1. Install dependencies

```bash
cd frontend/cleanup-crew
npm install
```

### 2. Configure environment variables

Create `frontend/cleanup-crew/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Start the dev server

```bash
npm run dev
```

App available at: `http://localhost:3000`

---

## API Endpoints

### Auth (`/auth`)

| Method | Path             | Auth     | Description              |
|--------|------------------|----------|--------------------------|
| POST   | `/auth/signup`   | Public   | Register a new user      |
| POST   | `/auth/login`    | Public   | Login, returns JWT       |
| GET    | `/auth/profile`  | Required | Get current user profile |

### Admin (`/admin`)

| Method | Path                       | Auth  | Description         |
|--------|----------------------------|-------|---------------------|
| GET    | `/admin/users`             | Admin | List all users      |
| DELETE | `/admin/users/{id}`        | Admin | Delete a user       |
| PATCH  | `/admin/users/{id}/role`   | Admin | Update a user role  |

---

## Backend Architecture

The backend follows a three-layer separation of concerns:

```
api/        → HTTP request/response handling only
services/   → Business logic
repositories/ → Database access only
```

---

## Authentication Flow

1. User signs up at `/signup` → account created
2. User logs in at `/login` → JWT stored in `localStorage`
3. JWT attached to all subsequent API requests via `Authorization: Bearer`
4. Protected pages redirect to `/login` if no valid token is present
5. A 401 response from the API clears the token and redirects to `/login`

### Roles

| Role    | Access                                  |
|---------|-----------------------------------------|
| `USER`  | Own profile                             |
| `ADMIN` | All users, role management, user deletion |
