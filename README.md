# Meal Planner

A web-based meal planning application built with Django, Django REST Framework, and Tailwind CSS.

## Tech Stack

- **Backend**: Django 6, Django REST Framework, Gunicorn
- **Database**: PostgreSQL (via Neon) in production, SQLite locally
- **Frontend**: Tailwind CSS
- **Static files**: WhiteNoise
- **Deployment**: Docker, Render

## Prerequisites

- Python 3.13+
- Node.js (for Tailwind)
- Docker and Docker Compose (optional, for containerized dev)

## Local Setup

```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node dependencies
npm install

# Configure environment
cp .env.example .env   # or create one with the keys below

# Run migrations and start the server
python manage.py migrate
python manage.py runserver
```

### Required environment variables

| Variable       | Description                          | Example            |
|----------------|--------------------------------------|--------------------|
| `SECRET_KEY`   | Django secret key (required)         | `django-insecure-...` |
| `DEBUG`        | Debug mode, default `False`          | `True`             |
| `ALLOWED_HOSTS`| Comma-separated allowed hosts        | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL (optional, uses SQLite if unset) | `postgres://user:pass@host/db` |

## Docker (local)

```bash
docker compose up --build
```

The app will be available at http://localhost:8000. SQLite data persists via the `db.sqlite3` volume.

## Deploying to Render

The `render.yaml` blueprint deploys this project as a Docker service.

### Option A: Blueprint (recommended)

1. Push this repository to GitHub.
2. In Render, go to **New > Blueprint** and connect the repository.
3. Render reads `render.yaml`, creates the `meal-planner` web service, and generates `SECRET_KEY`.
4. Set the following env vars in the Render dashboard (Blueprint syncs these):
   - `ALLOWED_HOSTS` — your app URL, e.g. `myapp.onrender.com`
   - `DATABASE_URL` — your Neon connection string (append `?sslmode=require`)
5. Deploy. Render builds the Docker image, runs migrations, and serves the app with Gunicorn.

### Option B: Manual

1. In Render, go to **New > Web Service** and connect your repo.
2. Choose **Docker** as the runtime; Render auto-detects the `Dockerfile`.
3. Add the env vars from the table above.
4. Deploy.

### Notes

- Render's filesystem is ephemeral, so production data lives in Neon via `DATABASE_URL`. Do not rely on `db.sqlite3` in production.
- Migrations and `collectstatic` run automatically during the Docker image startup.
