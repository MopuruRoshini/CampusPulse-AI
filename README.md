# CampusPulse AI

A campus incident-management prototype with a React dashboard and a FastAPI backend. It demonstrates how a reported campus issue can move through four named workflow roles: Pulse, Sherlock, Fixer and Guardian.

> **Implementation status:** The workflow currently runs as a deterministic demo in the CampusPulse backend. The four roles are represented in the demo workflow; they are not currently running as autonomous AI agents or communicating through a live Switch room.

## What is implemented

- React, TypeScript and Vite dashboard.
- FastAPI backend with incident-related API endpoints.
- Persistent incident, approval and activity records using SQLAlchemy.
- Demo incident workflow with four stages:
  - **Pulse:** incident classification and priority.
  - **Sherlock:** investigation summary.
  - **Fixer:** proposed troubleshooting action.
  - **Guardian:** risk review and approval request.
- Approval workflow for reviewing a proposed action.
- Switch protocol client foundation in the backend.
- Discord bot intake code is present, but a live Discord-to-Switch workflow has not been configured or verified.

The demo scenario used during development is a Wi-Fi issue in CSE Block, Room 302. Demo outputs are simulated; the application does not currently read live campus network telemetry or verify that a physical issue has been fixed.

## Current architecture

The verified demo path is:

```text
User
  |
  v
React + TypeScript dashboard
  |
  v
FastAPI backend
  |
  v
Deterministic demo workflow
  |
  +--> Pulse stage
  +--> Sherlock stage
  +--> Fixer stage
  +--> Guardian stage
  |
  v
Incident / approval / activity records
```

## Planned integration (not yet verified)

The repository includes a Switch room template and a backend Switch protocol client foundation. The intended future setup is to connect the four roles through a Switch shared room. A live Switch server connection, agent registration, room membership, message exchange and end-to-end agent handoff have **not** been verified for this project.

The Discord bot code is also not evidence of a working Discord-to-Switch integration. Do not treat the current demo workflow as proof of live Switch usage.

## Technology

- Frontend: React, TypeScript, Vite
- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- Database: SQLite by default
- Other code included: Switch protocol client foundation and Discord bot intake foundation

## Run locally

### Backend (Ubuntu / WSL)

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
python -m pytest -q
python run.py
```

The API runs at http://localhost:8000.

- API health: http://localhost:8000/api/health
- API documentation: http://localhost:8000/docs

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

If using the Ubuntu/WSL environment where the npm executable is available through Node's npm CLI:

```bash
node /usr/share/nodejs/npm/bin/npm-cli.js install
node /usr/share/nodejs/npm/bin/npm-cli.js run dev
```

The Vite development server runs at http://localhost:5173.

## Demo workflow

1. Start the backend and frontend.
2. Open the dashboard and go to **Incidents**.
3. Select **Report incident**.
4. Try this example: `Wi-Fi has stopped working in CSE Block, Room 302 before an online examination.`
5. Open the created incident and review the demo activity for Pulse, Sherlock, Fixer and Guardian.
6. Open **Approvals** to review the proposed action.

The workflow is a deterministic demonstration. It does not establish that live AI agents independently performed these steps.

## Verification performed during development

- Backend test command: `python -m pytest -q` — **2 tests passed**.
- Frontend production build: `tsc --noEmit && vite build` — completed successfully.
- Backend API health endpoint was checked successfully.
- FastAPI Swagger documentation at `/docs` was opened successfully.

These checks verify the local development build and the tests that were run. They do not verify live Switch, Discord, autonomous agent communication or production deployment.

## Known limitations

- Live Switch connection and end-to-end agent communication are not configured or verified.
- The four workflow roles currently run as a deterministic demo, not autonomous AI agents.
- Discord-to-Switch integration is not complete or verified.
- Live campus network or facilities data is not connected.
- Authentication and role-based access control are not implemented.
- Production deployment and security readiness have not been verified.

## Repository contents

See the source folders for the frontend, backend, Switch room template and integration foundations.

