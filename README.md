# 🤖 RoboFleet

A production-ready fleet management API for autonomous robots. Built with FastAPI, PostgreSQL, Redis, Celery, and WebSockets.

**Portfolio project demonstrating:** async Python, real-time communication, background task processing, JWT auth with RBAC, and clean architecture patterns.

## ✨ Features

- **🤖 Robot Management** — Full CRUD with status tracking (idle, active, charging, maintenance, offline)
- **📋 Mission Control** — Create, assign, and track missions through their lifecycle
- **⚡ Real-time Updates** — WebSocket connections for live robot/fleet status
- **⏰ Background Tasks** — Celery workers for async operations + scheduled health checks
- **🔐 Authentication** — JWT-based auth with role-based access (viewer/operator/admin)
- **📚 Auto Documentation** — OpenAPI/Swagger UI at `/docs`

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL + SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Cache/Broker | Redis |
| Task Queue | Celery + Celery Beat |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt |
| Containers | Docker + docker compose |

## 🎬 Live Demo

Run the interactive demo to see all features in action:

```bash
# Start services first
docker-compose up -d
docker-compose exec api alembic upgrade head

# Run the demo
./scripts/run-demo.sh
```

The demo walks through: authentication → robot management → mission lifecycle → background tasks → WebSocket info.

## 🚀 Quick Start

### Using Docker (recommended)

```bash
# Clone the repo
git clone https://github.com/ibrahimsel/robofleet.git
cd robofleet

# Copy environment file
cp .env.example .env

# Start all services (api, db, redis, celery-worker, celery-beat)
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# API is now live!
# 📖 Docs: http://localhost:8000/docs
# 🔌 API:  http://localhost:8000/api/v1
```

### Local Development

<details>
<summary><b>Using uv (fast, recommended)</b></summary>

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Start PostgreSQL and Redis (or use Docker for just those)
docker compose up -d db redis

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload
```
</details>

<details>
<summary><b>Using pip</b></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL and Redis
docker compose up -d db redis

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload
```
</details>

## 📖 API Usage

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "pilot@robofleet.io", "password": "securepass123"}'

# Login and get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=pilot@robofleet.io&password=securepass123"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# Use the token in subsequent requests
export TOKEN="eyJ..."
```

### Robot Management

```bash
# Create a robot (requires operator/admin role)
curl -X POST http://localhost:8000/api/v1/robots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scout-01",
    "serial_number": "RBT-2024-001",
    "robot_type": "drone",
    "status": "idle"
  }'

# List all robots
curl http://localhost:8000/api/v1/robots \
  -H "Authorization: Bearer $TOKEN"

# Get specific robot
curl http://localhost:8000/api/v1/robots/{robot_id} \
  -H "Authorization: Bearer $TOKEN"

# Update robot status
curl -X PATCH http://localhost:8000/api/v1/robots/{robot_id}/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

### Mission Control

```bash
# Create a mission
curl -X POST http://localhost:8000/api/v1/missions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Warehouse Patrol",
    "description": "Routine security sweep of sector A",
    "priority": 2
  }'

# Assign a robot to a mission
curl -X POST http://localhost:8000/api/v1/missions/{mission_id}/assign \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "{robot_id}"}'

# Start the mission
curl -X POST http://localhost:8000/api/v1/missions/{mission_id}/start \
  -H "Authorization: Bearer $TOKEN"

# Complete the mission
curl -X POST http://localhost:8000/api/v1/missions/{mission_id}/complete \
  -H "Authorization: Bearer $TOKEN"
```

### Mission Lifecycle

```
pending → assigned → in_progress → completed
                  ↘ failed ↙
                  ↘ cancelled
```

## 🔌 WebSocket API

Connect to WebSockets for real-time updates:

### Single Robot Updates

```javascript
// Connect to a specific robot's updates
const ws = new WebSocket('ws://localhost:8000/ws/robots/{robot_id}?token={jwt_token}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Robot update:', data);
  // { "robot_id": "...", "status": "active", "battery_level": 85, ... }
};
```

### Fleet-wide Updates

```javascript
// Connect to all fleet updates
const ws = new WebSocket('ws://localhost:8000/ws/fleet?token={jwt_token}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Fleet update:', data);
  // { "event": "status_change", "robot_id": "...", "data": {...} }
};
```

### Python WebSocket Client

```python
import asyncio
import websockets

async def listen():
    uri = "ws://localhost:8000/ws/fleet?token=YOUR_JWT_TOKEN"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            print(f"Received: {message}")

asyncio.run(listen())
```

## ⏰ Background Tasks

RoboFleet uses Celery for background processing:

### Async Tasks

| Task | Description |
|------|-------------|
| `send_robot_command` | Queue commands to robots |
| `schedule_mission` | Process mission scheduling |

### Scheduled Tasks (Celery Beat)

| Schedule | Task | Description |
|----------|------|-------------|
| Every 60s | `check_fleet_health` | Monitor all robots, flag issues |

### Triggering Tasks Manually

```bash
# Via API endpoint
curl -X POST http://localhost:8000/api/v1/tasks/fleet-health-check \
  -H "Authorization: Bearer $TOKEN"

# Response: {"task_id": "abc-123", "status": "queued"}
```

## 🔐 Role-Based Access Control

| Role | Permissions |
|------|-------------|
| `viewer` | Read robots, missions |
| `operator` | + Create/update robots, manage missions |
| `admin` | + Delete robots, manage users |

New users are assigned `viewer` role by default.

## 📁 Project Structure

```
robofleet/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py        # Login, register
│   │   │   ├── robots.py      # Robot CRUD
│   │   │   ├── missions.py    # Mission management
│   │   │   ├── tasks.py       # Task triggers
│   │   │   └── websocket.py   # WS endpoints
│   │   └── deps.py            # Auth & DB dependencies
│   ├── core/
│   │   ├── config.py          # Settings (pydantic-settings)
│   │   ├── security.py        # JWT & password hashing
│   │   └── websocket.py       # Connection manager
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── tasks/                 # Celery task definitions
│   ├── db/                    # Database setup
│   ├── worker.py              # Celery app config
│   └── main.py                # FastAPI app
├── alembic/                   # Database migrations
├── tests/                     # pytest test suite
├── scripts/
│   └── ws_client.py           # WebSocket test client
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## 🧪 Running Tests

```bash
# With Docker
docker compose exec api pytest

# Local (with uv)
uv run pytest -v

# Local (with pip)
pytest -v

# With coverage
pytest --cov=app --cov-report=term-missing
```

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI application |
| `db` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis (cache + Celery broker) |
| `celery-worker` | — | Background task processor |
| `celery-beat` | — | Scheduled task scheduler |

```bash
# View logs
docker compose logs -f api celery-worker

# Restart a service
docker compose restart api

# Stop everything
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT signing key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |

See `.env.example` for a complete template.

## 🗺 Roadmap

- [ ] Prometheus metrics endpoint
- [ ] Rate limiting
- [ ] API key authentication (for robot agents)
- [ ] Mission waypoints and path planning
- [ ] Fleet analytics dashboard

## 📄 License

MIT

---

Built by [Ibrahim Sel](https://github.com/ibrahimsel) • [View on GitHub](https://github.com/ibrahimsel/robofleet)
