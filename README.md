# Kerala Cleanup Platform - Backend API

A privacy-first, production-ready FastAPI backend for managing volunteer cleanup drives across Kerala with plans for national expansion.

## 🎯 Key Features

### Privacy & Compliance
- ✅ **Age-band collection** (under13, 13-17, 18+) instead of DOB
- ✅ **Guardian consent** required for minors (COPPA compliant)
- ✅ **Minimal data exposure** to organizers (first name + age band only)
- ✅ **No CSV exports** to prevent data harvesting
- ✅ **In-app messaging proxy** (no direct contact info sharing)

### Security (OWASP API Top 10 Compliant)
- ✅ JWT authentication with access + refresh tokens
- ✅ Role-based access control (volunteer, organizer, admin)
- ✅ Password hashing with bcrypt
- ✅ NoSQL injection prevention
- ✅ Rate limiting (60 requests/minute)
- ✅ HTTPS-only cookies
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ Structured logging with request IDs

### Business Logic
- ✅ Drive search by district, type, date range
- ✅ Auto-close registrations (deadline + capacity)
- ✅ Attendance tracking with volunteer hours
- ✅ Pagination on all list endpoints
- ✅ Geospatial queries (location-based search)

## 🏗️ Architecture

```
app/
├── core/
│   ├── config.py           # Environment-based configuration
│   ├── security.py         # JWT, password hashing, sanitization
│   └── dependencies.py     # Auth dependencies, RBAC
├── models/
│   ├── user.py            # Pydantic user schemas
│   ├── drive.py           # Pydantic drive schemas
│   └── registration.py    # Pydantic registration schemas
├── repositories/
│   ├── user_repository.py        # User data access
│   ├── drive_repository.py       # Drive data access
│   └── registration_repository.py # Registration data access
├── routers/
│   ├── auth.py            # Registration, login
│   ├── users.py           # User profile management
│   ├── drives.py          # Drive CRUD
│   ├── registrations.py   # Volunteer registration
│   └── organizer.py       # Organizer dashboard
├── database.py            # MongoDB connection
└── main.py                # FastAPI app + middleware
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- MongoDB 7.0+ (or use Docker)

### 1. Clone & Setup

```bash
# Clone repository
git clone <repo-url>
cd cleanup-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# CRITICAL: Change JWT secret in production!
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters-long

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=cleanup_platform

# Environment
ENVIRONMENT=development  # or "production"
```

### 3. Start with Docker Compose

```bash
# Start MongoDB + API
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

API will be available at: `http://localhost:8000`

### 4. Manual Start (without Docker)

```bash
# Start MongoDB separately
mongod --dbpath /path/to/data

# Run FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Authentication Flow

1. **Register User**
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "Arjun Menon",
  "email": "arjun@example.com",
  "phone": "+919876543210",
  "age_band": "18+",
  "password": "SecurePass123",
  "consent_flags": {
    "terms_accepted": true,
    "privacy_accepted": true,
    "guardian_consent": null
  }
}
```

2. **Login**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "arjun@example.com",
  "password": "SecurePass123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

3. **Use Token**
```bash
GET /api/v1/users/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Core Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register new user |
| POST | `/api/v1/auth/login` | No | Login and get tokens |
| GET | `/api/v1/users/me` | Yes | Get current user profile |
| PATCH | `/api/v1/users/me` | Yes | Update profile |
| GET | `/api/v1/drives/` | No | Search drives (public) |
| POST | `/api/v1/drives/` | Organizer | Create drive |
| GET | `/api/v1/drives/{id}` | No | Get drive details |
| PATCH | `/api/v1/drives/{id}` | Organizer | Update drive |
| POST | `/api/v1/registrations/` | Yes | Register for drive |
| GET | `/api/v1/registrations/my` | Yes | My registrations |
| DELETE | `/api/v1/registrations/{id}` | Yes | Cancel registration |
| GET | `/api/v1/organizer/drives` | Organizer | My organized drives |
| GET | `/api/v1/organizer/{id}/participants` | Organizer | Drive participants |
| POST | `/api/v1/organizer/attendance/{id}/mark` | Organizer | Mark attendance |

## 🧪 Sample API Requests

### Create a Cleanup Drive

```bash
POST /api/v1/drives/
Authorization: Bearer <organizer-token>
Content-Type: application/json

{
  "title": "Varkala Beach Cleanup Drive",
  "description": "Join us for a morning beach cleanup at Varkala. We'll provide gloves and bags. Breakfast included!",
  "type": "beach_cleanup",
  "date_time": "2026-02-15T07:00:00Z",
  "location": {
    "geo": {
      "type": "Point",
      "coordinates": [76.7174, 8.7379]
    },
    "address": "Varkala Beach, Near Cliff Side",
    "district": "Thiruvananthapuram",
    "state": "Kerala"
  },
  "max_volunteers": 50
}
```

### Search Drives

```bash
GET /api/v1/drives/?district=Ernakulam&type=beach_cleanup&date_from=2026-02-01&page=1&page_size=20
```

### Register for Drive

```bash
POST /api/v1/registrations/
Authorization: Bearer <user-token>
Content-Type: application/json

{
  "drive_id": "65f1a2b3c4d5e6f7g8h9i0j1"
}
```

### Mark Attendance

```bash
POST /api/v1/organizer/attendance/65f1a2b3c4d5e6f7g8h9i0j1/mark
Authorization: Bearer <organizer-token>
Content-Type: application/json

{
  "user_id": "65f1a2b3c4d5e6f7g8h9i0j2",
  "attended": true,
  "hours_logged": 3.5
}
```

## 🔐 Security Best Practices

### JWT Token Management
- **Access tokens**: 30 minutes expiry
- **Refresh tokens**: 7 days expiry
- Store refresh tokens in httpOnly cookies
- Rotate tokens on refresh

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- Hashed with bcrypt (automatic salting)

### NoSQL Injection Prevention
```python
# All user inputs sanitized before queries
# Removes MongoDB operators: $gt, $lt, $ne, $where, etc.
safe_query = sanitize_mongo_query(user_input)
```

### Rate Limiting
- 60 requests per minute per IP
- Applied globally to all endpoints
- Returns 429 Too Many Requests when exceeded

## 📊 Database Schema

### Users Collection
```javascript
{
  _id: "ObjectId",
  name: "string",
  email: "string (unique, lowercase)",
  phone: "string (unique, E164 format)",
  age_band: "under13 | 13-17 | 18+",
  hashed_password: "string (bcrypt)",
  roles: ["volunteer", "organizer", "admin"],
  consent_flags: {
    terms_accepted: boolean,
    privacy_accepted: boolean,
    guardian_consent: boolean?
  },
  is_active: boolean,
  created_at: ISODate,
  updated_at: ISODate
}
```

### Drives Collection
```javascript
{
  _id: "ObjectId",
  title: "string",
  description: "string",
  type: "beach_cleanup | river_cleanup | ...",
  date_time: ISODate,
  location: {
    geo: { type: "Point", coordinates: [lon, lat] },
    address: "string",
    district: "Kerala district name",
    state: "Kerala"
  },
  max_volunteers: number,
  organizer_id: "ObjectId",
  status: "draft | published | ongoing | completed | cancelled",
  current_volunteers: number,
  registration_open: boolean,
  created_at: ISODate,
  updated_at: ISODate
}
```

### Registrations Collection
```javascript
{
  _id: "ObjectId",
  drive_id: "ObjectId",
  user_id: "ObjectId",
  status: "confirmed | cancelled | waitlist",
  created_at: ISODate
}
// Unique index on (drive_id, user_id)
```

### Attendance Collection
```javascript
{
  _id: "ObjectId",
  drive_id: "ObjectId",
  user_id: "ObjectId",
  attended: boolean,
  hours_logged: number?,
  marked_by: "ObjectId (organizer)",
  marked_at: ISODate
}
// Unique index on (drive_id, user_id)
```

## 🧰 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Formatting
```bash
# Install formatters
pip install black isort

# Format code
black app/
isort app/
```

### Type Checking
```bash
# Install mypy
pip install mypy

# Check types
mypy app/
```

## 📈 Monitoring & Logging

### Structured Logs
All logs include request IDs for tracing:
```
2026-01-05 10:30:15 - app.main - INFO - [a1b2c3d4-e5f6-7890] - POST /api/v1/drives/
```

### Health Check Monitoring
```bash
# Check service health
curl http://localhost:8000/health

Response:
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

## 🚧 Production Deployment

### Environment Variables (Production)
```bash
# Generate strong JWT secret (32+ characters)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Set to production
ENVIRONMENT=production

# Use production MongoDB with authentication
MONGODB_URL=mongodb://user:password@prod-mongo:27017/cleanup_platform?authSource=admin

# Restrict CORS origins
ALLOWED_ORIGINS=https://yourdomain.com

# Increase rate limit for production
RATE_LIMIT_PER_MINUTE=120
```

### Docker Production Build
```bash
# Build production image
docker build -t cleanup-api:prod .

# Run with production env
docker run -d \
  --name cleanup-api \
  -p 8000:8000 \
  --env-file .env.production \
  cleanup-api:prod
```

### Recommended Infrastructure
- **Load Balancer**: Nginx/HAProxy with SSL termination
- **Database**: MongoDB Atlas or self-hosted replica set
- **Caching**: Redis for rate limiting and session storage
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 👥 Support

For issues and questions:
- GitHub Issues: [Repository Issues](https://github.com/yourusername/cleanup-platform/issues)
- Email: support@cleanupplatform.org

---

**Built with ❤️ for Kerala's environment**