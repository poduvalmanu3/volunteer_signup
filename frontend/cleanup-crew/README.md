# Cleanup Crew — Frontend

Next.js web app for the Cleanup Crew platform.

## Tech Stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- CSS Modules
- react-hook-form

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Run the dev server

```bash
npm run dev
```

App available at: `http://localhost:3000`

## Pages

| Route     | Access    | Description       |
|-----------|-----------|-------------------|
| `/`       | Protected | Home dashboard    |
| `/login`  | Guest     | Login form        |
| `/signup` | Guest     | Registration form |

## Auth

- JWT stored in `localStorage` after login
- `AuthContext` exposes `isAuthenticated`, `isLoading`, `login()`, `logout()`
- `ProtectedRoute` wraps pages that require authentication
- `isLoading` prevents redirect flash on page refresh
- 401 API responses auto-clear the token and redirect to `/login`

## Project Structure

```
app/
├── layout.tsx          # Root layout with AuthProvider
├── page.tsx            # Protected home page
├── auth.module.css     # Shared auth page styles
├── login/
│   └── page.tsx        # Login form
└── signup/
    └── page.tsx        # Signup form
lib/
├── api.ts              # Fetch wrapper with JWT injection and 401 handling
├── AuthContext.tsx     # Global auth state
└── ProtectedRoute.tsx  # Route guard component
```
