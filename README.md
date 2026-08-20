# Pharma BrandPlan AI

This project is a FastAPI + Next.js application for pharmaceutical brand planning, scientific intelligence, competitor analysis, and launch planning.

## Architecture

- Backend: FastAPI application in `backend/app`
- Frontend: Next.js app in `frontend/src`
- Database: SQLite file stored in `backend/data/brandplan.db`
- Test stack: `pytest` for backend, `jest` for frontend

## Local setup

1. Create the backend virtual environment and install dependencies:

```bash
cd /Users/animeshmishra/Molecule\ to\ market\ AI
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

2. Copy environment examples if you want custom settings:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. Start the backend:

```bash
cd backend
python run.py
```

The API runs at `http://localhost:8000` by default.

4. In a second terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:3000` and uses `NEXT_PUBLIC_API_BASE` to reach the backend.

## Environment variables

Backend:

- `APP_ENV` (`development`/`production`)
- `PORT` (default `8000`)
- `CORS_ORIGINS` (comma-separated allowed frontend origins)
- `DATABASE_URL` (optional override for DB location)
- `OPENAI_API_KEY` (optional, for future live AI integrations)

Frontend:

- `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`)
- `NEXT_PUBLIC_APP_ENV`

## Core workflows

- Create a project from the home page
- Open a project workspace
- Review molecule intelligence, evidence, trials, regulatory, trademark, competitor, and forecast modules
- Generate a brand plan and creative assets
- Export DOCX/PPTX/XLSX artifacts from the report center

## Testing

```bash
cd backend
. .venv/bin/activate
pytest -q

cd ../frontend
npm test -- --runInBand
npm run build
```

## Docker

This repository includes Dockerfiles for both services. The local compose file is set up for development:

```bash
cd /Users/animeshmishra/Molecule\ to\ market\ AI
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Staging deployment (Render)

This repo includes a Render deployment blueprint in [render.yaml](render.yaml). It is ready for a manual staging setup on Render.

1. Create a new Render account and connect this GitHub repository.
2. In the Render dashboard, create the backend service using the `backend` root directory and the Python environment.
3. Set the following environment variables for the backend:

```bash
APP_ENV=production
PORT=8000
CORS_ORIGINS=https://<frontend-service-name>.onrender.com
DATABASE_URL=
OPENAI_API_KEY=
```

4. Create the frontend service using the `frontend` root directory and the Node environment.
5. Set the frontend environment variable:

```bash
NEXT_PUBLIC_API_BASE=https://<backend-service-name>.onrender.com
NEXT_PUBLIC_APP_ENV=production
```

6. Redeploy both services.

## Deployment notes

- Use a managed PostgreSQL or SQLite file for production if the project is expanded beyond local development.
- Keep secrets in the deployment platform's secrets manager instead of committing them.
- Set `CORS_ORIGINS` to the exact production frontend host(s) rather than wildcard origins.
- Use a production build of the Next.js app and run it behind a reverse proxy or container orchestration layer.

## CI

The repo includes GitHub Actions workflows under `.github/workflows` for CI and image publishing.

