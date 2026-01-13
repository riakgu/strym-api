# Strym API


## Overview
Strym API is a real-time log monitoring system built with FastAPI and TimescaleDB.
It provides log ingestion, querying, analytics, and WebSocket streaming with Redis-powered caching and pub/sub.

### Built With
[![Python][Python]][Python-url] [![FastAPI][FastAPI]][FastAPI-url] [![TimescaleDB][TimescaleDB]][TimescaleDB-url] [![Redis][Redis]][Redis-url]


## Features

- **Log Ingestion** - Single and bulk log ingestion
- **Log Query** - Filtered queries with pagination and full-text search
- **Statistics** - Summary and time-series analytics
- **Real-time Streaming** - WebSocket-based live log streaming
- **Redis Caching** - Query result caching with automatic invalidation
- **Redis Pub/Sub** - Multi-instance streaming support
- **Rate Limiting** - Per-IP request limiting
- **API Key Auth** - Simple authentication for all endpoints


## Getting Started

### Prerequisites
* Python >= 3.12
* PostgreSQL/TimescaleDB
* Redis

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/riakgu/strym-api.git
   cd strym-api
   ```

2. Install dependencies
   ```sh
   uv sync
   ```

3. Set up environment variables
   ```sh
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```env
   APP_NAME=Strym API
   DEBUG=true
   DATABASE_URL=postgresql://postgres:password@localhost:5432/strym
   REDIS_URL=redis://localhost:6379/0
   API_KEY=your-api-key
   ```

4. Run migrations
   ```sh
   psql $DATABASE_URL -f app/db/migrations/001_initial_schema.sql
   ```

5. Start the application
   ```sh
   # Development
   uv run uvicorn app.main:app --reload --port 8000
   ```

### Docker

Run with Docker Compose:
```sh
docker compose up -d
```

Build and run after code changes:
```sh
docker compose up -d --build
```


## API Reference

Full API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Quick Example

```sh
# Ingest log
curl -X POST http://localhost:8000/logs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"source":{"app_id":"my-app"},"severity":"info","message":"Hello"}'
```

### WebSocket Streaming

```javascript
const ws = new WebSocket('ws://localhost:8000/stream?api_key=your-key');

ws.send(JSON.stringify({
  type: 'subscribe',
  subscription_id: 'sub-1',
  filters: { severity: ['error', 'fatal'] }
}));

ws.onmessage = (e) => console.log(JSON.parse(e.data));
```


## Running Tests

```sh
uv run pytest
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://python.org/
[FastAPI]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[TimescaleDB]: https://img.shields.io/badge/TimescaleDB-FDB515?style=for-the-badge&logo=timescale&logoColor=black
[TimescaleDB-url]: https://www.timescale.com/
[Redis]: https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white
[Redis-url]: https://redis.io/
