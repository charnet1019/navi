# Navi Backend

FastAPI-based backend for the Navi navigation and link management system.

## Overview

The backend provides a RESTful API with JWT authentication, role-based access control, and comprehensive data management capabilities.

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database with async support via asyncpg
- **Redis**: Caching and session management
- **SQLAlchemy 2.0**: Async ORM for database operations
- **Alembic**: Database migration tool
- **Pydantic**: Data validation and settings management
- **JWT**: Token-based authentication
- **Uvicorn**: ASGI server

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API endpoint handlers
│   │       │   ├── auth.py     # Authentication endpoints
│   │       │   ├── users.py    # User management
│   │       │   ├── roles.py    # Role management
│   │       │   ├── permissions.py # Permission management
│   │       │   └── navigation.py  # Navigation endpoints
│   │       └── router.py       # API router configuration
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   ├── security.py        # Security utilities
│   │   └── dependencies.py    # FastAPI dependencies
│   ├── models/
│   │   ├── user.py           # User model
│   │   ├── role.py           # Role model
│   │   ├── permission.py     # Permission model
│   │   └── navigation.py     # Navigation model
│   ├── schemas/
│   │   ├── user.py           # User schemas
│   │   ├── role.py           # Role schemas
│   │   ├── permission.py     # Permission schemas
│   │   ├── navigation.py     # Navigation schemas
│   │   └── token.py          # Token schemas
│   ├── services/
│   │   ├── auth.py           # Authentication service
│   │   ├── user.py           # User service
│   │   ├── role.py           # Role service
│   │   └── navigation.py     # Navigation service
│   ├── database.py           # Database configuration
│   ├── redis.py              # Redis configuration
│   └── main.py               # Application entry point
├── alembic/
│   ├── versions/             # Migration files
│   └── env.py               # Alembic configuration
├── tests/
│   ├── conftest.py          # Test configuration
│   └── test_*.py            # Test files
├── uploads/                 # File upload directory
├── Dockerfile              # Production Docker image
├── Dockerfile.dev          # Development Docker image
├── requirements.txt        # Python dependencies
└── alembic.ini            # Alembic configuration
```

## Setup

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp ../.env.example ../.env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
# From project root
docker-compose -f docker-compose.dev.yml up backend
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users` - List users (admin only)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

### Roles
- `GET /api/v1/roles` - List roles
- `POST /api/v1/roles` - Create role (admin only)
- `GET /api/v1/roles/{id}` - Get role by ID
- `PUT /api/v1/roles/{id}` - Update role (admin only)
- `DELETE /api/v1/roles/{id}` - Delete role (admin only)

### Permissions
- `GET /api/v1/permissions` - List permissions
- `POST /api/v1/permissions` - Create permission (admin only)

### Navigation
- `GET /api/v1/navigation` - List navigation items
- `POST /api/v1/navigation` - Create navigation item
- `GET /api/v1/navigation/{id}` - Get navigation item
- `PUT /api/v1/navigation/{id}` - Update navigation item
- `DELETE /api/v1/navigation/{id}` - Delete navigation item

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current version
```bash
alembic current
```

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_auth.py
```

## Configuration

Configuration is managed through environment variables and the `app/core/config.py` file.

### Key Configuration Options

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token lifetime
- `DEBUG`: Enable debug mode
- `CORS_ORIGINS`: Allowed CORS origins, default `*`
- `CORS_ALLOW_CREDENTIALS`: Allow credentialed CORS requests when `CORS_ORIGINS` is not `*`
- `AUTH_COOKIE_SECURE`: Set auth cookies as Secure; use `true` on HTTPS production
- `AUTH_COOKIE_SAMESITE`: Auth cookie SameSite policy; default `lax`
- `AUTH_COOKIE_DOMAIN`: Optional cookie domain for shared subdomains
- `AUTH_CSRF_COOKIE_NAME` / `AUTH_CSRF_HEADER_NAME`: CSRF double-submit cookie/header names
- `LOG_LEVEL`: Logging level

## Security

### Authentication Flow

1. User registers or logs in with credentials
2. Server validates credentials and returns JWT tokens
3. Client stores tokens and includes access token in requests
4. Server validates token on each request
5. Client refreshes access token using refresh token when expired

### Password Security

- Passwords are hashed using bcrypt
- Minimum password requirements enforced
- Password reset functionality available

### RBAC System

- Users are assigned roles
- Roles have associated permissions
- Endpoints check for required permissions
- Hierarchical permission inheritance

## Caching

Redis is used for:
- Session management
- Token blacklisting
- Rate limiting
- Frequently accessed data caching

## Error Handling

The API uses standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

Error responses follow this format:
```json
{
  "detail": "Error message"
}
```

## Logging

Logs are configured based on the `LOG_LEVEL` environment variable.

Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Performance Optimization

- Async database operations
- Connection pooling
- Redis caching
- Query optimization with SQLAlchemy
- Lazy loading of relationships

## Development Guidelines

1. Follow PEP 8 style guide
2. Use type hints for all functions
3. Write docstrings for all public functions
4. Create tests for new features
5. Use async/await for I/O operations
6. Validate input with Pydantic schemas
7. Handle errors appropriately
8. Use dependency injection

## Troubleshooting

### Database connection errors
- Verify DATABASE_URL is correct
- Ensure PostgreSQL is running
- Check network connectivity

### Redis connection errors
- Verify REDIS_URL is correct
- Ensure Redis is running
- Check if Redis requires authentication

### Migration errors
- Check alembic.ini configuration
- Verify database permissions
- Review migration files for conflicts

### Import errors
- Ensure virtual environment is activated
- Verify all dependencies are installed
- Check Python version compatibility

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
