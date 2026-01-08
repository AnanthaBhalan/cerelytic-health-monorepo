# Cerelytic Health

Medical bill analysis platform for PM-JAY and insurance compliance.

## Quick Start

```bash
# From the infra directory
docker-compose up -d
```

This will start all services:
- Frontend: http://localhost:3000
- Manager API: http://localhost:8000
- Worker: http://localhost:8001
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Manager API**: FastAPI with PostgreSQL and Redis
- **Worker**: Background job processor with Redis queue
- **Database**: PostgreSQL
- **Queue**: Redis

## Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### API Development

```bash
cd manager-api
pip install -r requirements.txt
uvicorn main:app --reload
```

### Worker Development

```bash
cd worker
pip install -r requirements.txt
python worker.py
```

## API Endpoints

### Manager API

- `POST /bills` - Create a new bill for analysis
- `GET /bills/{bill_id}` - Get bill status and results
- `GET /healthz` - Health check

### Worker API

- `GET /healthz` - Health check

## Environment Variables

See `.env.example` files in each service for required environment variables.

## License

MIT
