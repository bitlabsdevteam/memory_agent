# Docker Setup for Trip Advisor AI Agent

This guide explains how to run the Trip Advisor AI Agent using Docker containers.

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- Environment variables configured (see `.env.example`)

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required: At least one LLM provider API key
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Default provider
DEFAULT_LLM_PROVIDER=google_gemini
```

### 2. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs/
- **Health Check**: http://localhost:5000/api/v1/health

## Individual Container Commands

### Backend Only

```bash
# Build backend image
docker build -t trip-advisor-backend .

# Run backend container
docker run -p 5000:5000 --env-file .env trip-advisor-backend
```

### Frontend Only

```bash
# Build frontend image
docker build -t trip-advisor-frontend ./frontend

# Run frontend container
docker run -p 3000:3000 trip-advisor-frontend
```

## Docker Compose Commands

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend

# Scale services (if needed)
docker-compose up --scale backend=2
```

## Service Configuration

### Backend Service
- **Port**: 5000
- **Health Check**: Enabled with curl
- **Environment**: Production mode
- **Volumes**: `.env` file mounted as read-only

### Frontend Service
- **Port**: 3000
- **Dependencies**: Waits for backend health check
- **Environment**: Production mode with API URL

## Troubleshooting

### Common Issues

1. **Port conflicts**: If ports 3000 or 5000 are in use, modify the port mappings in `docker-compose.yml`

2. **Environment variables**: Ensure your `.env` file is properly configured with valid API keys

3. **Build failures**: Check that all dependencies are properly installed

### Debugging

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs -f

# Execute commands in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# Restart specific service
docker-compose restart backend
```

### Health Checks

```bash
# Check backend health
curl http://localhost:5000/api/v1/health

# Check if frontend is responding
curl http://localhost:3000
```

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in your environment
2. Use proper secrets management instead of `.env` files
3. Configure proper logging and monitoring
4. Use a reverse proxy (nginx) for SSL termination
5. Consider using Docker Swarm or Kubernetes for orchestration

## Development Mode

For development with hot reloading, use the regular development setup instead of Docker, or modify the Dockerfiles to include volume mounts for source code.