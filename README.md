# 🤖 RoboFleet

A fleet management API for autonomous robots and vehicles. Built with FastAPI, PostgreSQL, Redis, and modern Python patterns.

## Features

- **Robot Management** — CRUD operations for robot fleet
- **Mission Control** — Create, assign, and track missions
- **Real-time Updates** — WebSocket connections for live robot status
- **Task Scheduling** — Background job processing with Celery
- **Authentication** — JWT-based auth with role-based access control

## Tech Stack

- **Framework:** FastAPI (async Python)
- **Database:** PostgreSQL with SQLAlchemy 2.0 (async)
- **Cache/Broker:** Redis
- **Task Queue:** Celery
- **Validation:** Pydantic v2
- **Auth:** JWT (python-jose)
- **Containers:** Docker + docker-compose

## Project Structure

```
robofleet/
├── app/
│   ├── api/              # API routes
│   │   ├── v1/
│   │   │   ├── robots.py
│   │   │   ├── missions.py
│   │   │   ├── auth.py
│   │   │   └── websocket.py
│   │   └── deps.py       # Dependencies (auth, db session)
│   ├── core/             # Config, security, constants
│   │   ├── config.py
│   │   └── security.py
│   ├── models/           # SQLAlchemy models
│   │   ├── robot.py
│   │   ├── mission.py
│   │   └── user.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── robot.py
│   │   ├── mission.py
│   │   └── user.py
│   ├── services/         # Business logic
│   │   ├── robot_service.py
│   │   └── mission_service.py
│   ├── db/               # Database setup
│   │   ├── base.py
│   │   └── session.py
│   └── main.py           # FastAPI app entry
├── tests/
├── alembic/              # DB migrations
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ibrahimsel/robofleet.git
cd robofleet

# Run with Docker
docker-compose up -d

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/robots` | GET | List all robots |
| `/api/v1/robots` | POST | Register new robot |
| `/api/v1/robots/{id}` | GET | Get robot details |
| `/api/v1/robots/{id}/status` | PATCH | Update robot status |
| `/api/v1/missions` | GET | List missions |
| `/api/v1/missions` | POST | Create mission |
| `/api/v1/missions/{id}/assign` | POST | Assign robot to mission |
| `/ws/robots/{id}` | WS | Real-time robot updates |

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/robofleet
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Development

### With Docker (recommended)

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api
```

### Local Development

#### Using uv (fast, recommended)

```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install dependencies
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[dev]"

# Run migrations (requires running PostgreSQL)
alembic upgrade head

# Run dev server
uvicorn app.main:app --reload
```

#### Using pip

```bash
# Create venv and install dependencies
python3 -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev]"

# Run migrations (requires running PostgreSQL)
alembic upgrade head

# Run dev server
uvicorn app.main:app --reload
```

### Running Tests

```bash
# With uv
uv run pytest

# With pip
pytest
```

## License

MIT
