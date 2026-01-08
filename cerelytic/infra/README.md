# Cerelytic Infrastructure

This directory contains the Docker Compose configuration for running the entire Cerelytic stack locally.

## Services

- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis queue (port 6379)  
- **manager-api**: FastAPI application (port 8000)
- **worker**: Background job processor
- **frontend**: Next.js application (port 3000)

## Quick Start

```bash
# From the infra directory
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Variables

The services use the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (change in production!)
- `NEXT_PUBLIC_API_URL`: Frontend API URL

## Development

Individual services can be restarted without affecting others:

```bash
docker-compose restart manager-api
docker-compose restart worker
```

## Database Access

Connect to PostgreSQL:
```bash
docker-compose exec postgres psql -U cerelytic -d cerelytic
```

Connect to Redis:
```bash
docker-compose exec redis redis-cli
```
