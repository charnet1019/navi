# Navi - Navigation & Link Management System

A modern, full-stack web application for managing navigation links with role-based access control (RBAC).

## Features

- **User Authentication**: Secure JWT-based authentication with access and refresh tokens
- **Role-Based Access Control**: Fine-grained permissions system with roles and permissions
- **Navigation Management**: Create, organize, and manage navigation links
- **Admin Dashboard**: Comprehensive admin interface for user and system management
- **Modern UI**: Built with Vue 3, Ant Design Vue, and TypeScript
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Caching**: Redis-based caching for improved performance
- **Docker Support**: Full containerization with Docker and Docker Compose

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database
- **Redis**: Caching and session management
- **SQLAlchemy**: ORM with async support
- **Alembic**: Database migrations
- **JWT**: Token-based authentication

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **TypeScript**: Type-safe development
- **Ant Design Vue**: UI component library
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **Axios**: HTTP client
- **Vite**: Build tool and dev server

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd navi
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start development environment:
```bash
./scripts/start-dev.sh
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Default Login

The initial database migration creates a default administrator account:

- Username: `admin`
- Password: `admin123`

Change this password immediately after first login, especially outside local development.

### Production Deployment

1. Configure environment variables in `.env`

2. Start production environment:
```bash
./scripts/start-prod.sh
```

3. Access the application:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000

## Project Structure

```
navi/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   │   ├── api/         # API routes
│   │   ├── core/        # Core functionality
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   ├── Dockerfile       # Production Docker image
│   └── requirements.txt # Python dependencies
├── frontend/            # Vue.js frontend
│   ├── src/            # Application code
│   │   ├── api/        # API client
│   │   ├── components/ # Vue components
│   │   ├── router/     # Route definitions
│   │   ├── stores/     # Pinia stores
│   │   ├── types/      # TypeScript types
│   │   └── views/      # Page components
│   ├── Dockerfile      # Production Docker image
│   └── package.json    # Node dependencies
├── scripts/            # Utility scripts
├── docker-compose.yml  # Production compose file
├── docker-compose.dev.yml # Development compose file
└── README.md          # This file
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `POSTGRES_PASSWORD`: Database password
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (change in production!)
- `DEBUG`: Enable debug mode (false in production)
- `CORS_ORIGINS`: Allowed CORS origins, default `*`
- `CORS_ALLOW_CREDENTIALS`: Allow credentialed CORS requests when `CORS_ORIGINS` is not `*`
- `AUTH_COOKIE_SECURE`: Set auth cookies as Secure; use `true` on HTTPS production
- `AUTH_COOKIE_SAMESITE`: Auth cookie SameSite policy; default `lax`
- `AUTH_COOKIE_DOMAIN`: Optional cookie domain for shared subdomains
- `AUTH_CSRF_COOKIE_NAME` / `AUTH_CSRF_HEADER_NAME`: CSRF double-submit cookie/header names

### HttpOnly Cookie Authentication

JWTs are stored in HttpOnly cookies and are not exposed to frontend JavaScript. Unsafe API requests use a double-submit CSRF token: the backend sets `AUTH_CSRF_COOKIE_NAME`, and the frontend sends the same value in `AUTH_CSRF_HEADER_NAME`. For HTTPS production set `AUTH_COOKIE_SECURE=true`; if frontend and backend are truly cross-site, use `AUTH_COOKIE_SAMESITE=none` with Secure cookies.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Docker Commands

### Development
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Rebuild images
docker-compose -f docker-compose.dev.yml build
```

### Production
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild images
docker-compose build --no-cache
```

## Security Considerations

1. **Change default credentials**: Update the default admin password, `SECRET_KEY`, and `POSTGRES_PASSWORD` in production
2. **Use HTTPS**: Configure SSL/TLS certificates for production
3. **Environment variables**: Never commit `.env` files to version control
4. **CORS configuration**: Set `CORS_ORIGINS` to your frontend origin(s) and keep `CORS_ALLOW_CREDENTIALS=true` when using a fixed domain
5. **Rate limiting**: Consider adding rate limiting for production
6. **Regular updates**: Keep dependencies up to date

## Troubleshooting

### Database connection issues
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database logs: `docker-compose logs postgres`
- Verify DATABASE_URL in .env

### Redis connection issues
- Ensure Redis container is running: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`
- Verify REDIS_URL in .env

### Frontend not loading
- Check if backend is running: `curl http://localhost:8000/health`
- Verify `CORS_ORIGINS` includes the frontend URL and `CORS_ALLOW_CREDENTIALS` is set appropriately
- Check browser console for errors

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

[Your Support Information Here]
