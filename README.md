# Three-Tier App
1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Local Development Setup](#4-local-dev-setup)
5. [Dockerizing the App](#dockerizing-the-app)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Errors & Fixes Log](#7-Errors-&-Fixes-Log)



## 1 Architecture Overview

┌─────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                │
│                  namespace: three-tier-app           │
│                                                     │
│  ┌──────────────────┐                               │
│  │  frontend Pod(s) │  NodePort :30080              │
│  │  nginx:alpine    │◄──────────────────── Browser  │
│  │  port 80         │                               │
│  └────────┬─────────┘                               │
│           │ /api/* → proxy_pass                     │
│           ▼                                         │
│  ┌──────────────────┐                               │
│  │  backend Pod(s)  │  ClusterIP (internal only)    │
│  │  FastAPI/uvicorn │  backend-service:8000         │
│  │  port 8000       │                               │
│  └────────┬─────────┘                               │
│           │ SQLAlchemy                              │
│           ▼                                         │
│  ┌──────────────────┐                               │
│  │  postgres Pod    │  ClusterIP (internal only)    │
│  │  postgres:15-alp │  postgres-service:5432        │
│  │  port 5432       │                               │
│  └──────────────────┘                               │
│           │                                         │
│  ┌────────▼─────────┐                               │
│  │  PersistentVolume│  1Gi — survives pod restarts  │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘


### Network Traffic Flow
### How a request travels through the app:

You open the app in your browser — your browser contacts the frontend (think of it as the shop's front door) and receives the React interface: the login page, buttons, forms.

nginx acts as a receptionist. Every request that arrives at the frontend is handled by nginx. If you're just navigating pages — nginx serves them directly from its shelf, fast, no questions asked.

When you submit a form (login, signup), nginx forwards it to the backend. Any request going to /api/ is passed through an internal corridor to FastAPI — your browser never knows the backend even exists at a separate address. It's like giving your order to a waiter who then walks to the kitchen; you never go to the kitchen yourself.

FastAPI is the kitchen. It processes your request — checks your password, creates your account, generates your login token — then sends back a JSON response (like a meal on a tray) which nginx passes back to your browser.

PostgreSQL is the filing cabinet. FastAPI reads from and writes to it whenever it needs to remember something — who you are, when you signed up. The data is stored on a dedicated disk space (PersistentVolumeClaim) that survives even if the database container is restarted, the same way a filing cabinet doesn't empty itself when the office closes for the night.



## 2. Technology Stack
Layer	Technology	Purpose
Frontend	React 18 + Vite	UI framework + fast dev build tool
Frontend serving	nginx:alpine	Serves static files + reverse proxy to backend
Backend	FastAPI (Python 3.11)	REST API framework
Backend server	uvicorn	ASGI server that runs FastAPI
ORM	SQLAlchemy 2.x	Maps Python classes to database tables
Database	PostgreSQL 15 (Alpine)	Relational database
Auth	JWT (python-jose) + bcrypt (passlib)	Stateless authentication
Containerization	Docker	Package app + dependencies into images
Orchestration	Kubernetes (minikube)	Manage, scale, and deploy containers
Secret encryption	Bitnami Sealed Secrets	Encrypt k8s Secrets for safe Git storage
Image registry	DockerHub (castromeka/)	Store and distribute Docker images


## 3 Project-structure
Three-TIER-APP/
├── README.md
├── .gitignore                        # Excludes .env files and secret-plain.yaml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt              # Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI app, route definitions, CORS
│       ├── models.py                 # SQLAlchemy ORM models (User table)
│       ├── schemas.py                # Pydantic request/response shapes
│       ├── auth.py                   # JWT creation/validation, bcrypt hashing
│       └── database.py               # Engine, session, Base setup
│
├── frontend/
│   ├── Dockerfile                    # Two-stage: node build → nginx serve
│   ├── nginx.conf                    # Custom nginx: SPA routing + /api/ proxy
│   ├── .dockerignore                 # Prevents .env from entering Docker build
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx                  # React entry point
│       ├── App.jsx                   # Router with PrivateRoute guard
│       ├── api.js                    # Axios instance with JWT interceptor
│       └── pages/
│           ├── Login.jsx
│           ├── Signup.jsx
│           └── Dashboard.jsx         # Protected — requires valid token
│
└── k8s/
    ├── namespace.yaml                # Creates namespace: three-tier-app
    ├── postgres/
    │   ├── configmap.yaml            # POSTGRES_DB=appdb (non-sensitive)
    │   ├── secret-plain.yaml         # GITIGNORED — plain text credentials
    │   ├── sealed-secret.yaml        # Committed — encrypted credentials
    │   ├── pvc.yaml                  # 1Gi persistent volume claim
    │   ├── deployment.yaml           # postgres:15-alpine, 1 replica
    │   └── service.yaml              # ClusterIP on port 5432
    ├── backend/
    │   ├── configmap.yaml            # JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
    │   ├── secret-plain.yaml         # GITIGNORED — DATABASE_URL, SECRET_KEY
    │   ├── sealed-secret.yaml        # Committed — encrypted
    │   ├── deployment.yaml           # castromeka/three-tier-backend:v2, 2 replicas
    │   └── service.yaml              # ClusterIP on port 8000
    └── frontend/
        ├── deployment.yaml           # castromeka/three-tier-frontend:v2, 2 replicas
        └── service.yaml              # NodePort 30080



## 4 Local Development Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (gitignored):
```
DATABASE_URL=postgresql://appuser:Password@localhost:5432/appdb
```

`backend/app/database.py` calls `load_dotenv()` so this is picked up automatically.

Run a local Postgres container matching the credentials above:
```bash
docker run -d \
  --name local-postgres \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD='Password' \
  -e POSTGRES_DB=appdb \
  -p 5432:5432 \
  postgres:15-alpine
```

Start the backend:
```bash
uvicorn app.main:app --reload --port 8000
```
Tables are auto-created on startup via `models.Base.metadata.create_all(bind=engine)`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env` (gitignored, **local dev only**):
```
VITE_API_URL=http://localhost:8000
```

`frontend/src/api.js` falls back to `/api` if `VITE_API_URL` isn't set — that fallback is what the production (Docker/k8s) build relies on.

---

## 5. Dockerizing the App

### Backend — `backend/Dockerfile`
Multi-stage not needed; simple `python:3.11-slim` image running `uvicorn`.

### Frontend — `frontend/Dockerfile`
Two-stage build:
1. `node:20-alpine` — `npm install && npm run build`
2. `nginx:alpine` — serves `/dist`, with custom `frontend/nginx.conf`

`frontend/nginx.conf`:
```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;   # React Router support
    }

    location /api/ {
        proxy_pass http://backend-service:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> `backend-service` is a Kubernetes Service DNS name — this config only resolves correctly inside the cluster (or a Docker network with a matching alias for local testing).

### `.dockerignore` (frontend)
Critical — without this, `frontend/.env` (with `VITE_API_URL=http://localhost:8000`) gets copied into the build context and **baked into the production JS bundle**, breaking the app in Docker/k8s.

```
node_modules
dist
.env
.env.local
```

### Build & Push to DockerHub

```bash
docker login

# Backend
docker build -t castromeka/three-tier-backend:latest ./backend
docker push castromeka/three-tier-backend:latest

# Frontend
docker build -t castromeka/three-tier-frontend:latest ./frontend
docker push castromeka/three-tier-frontend:latest
```

> When rebuilding after a code/dependency fix, bump the tag (`v2`, `v3`, ...) instead of reusing `:latest` — see [Errors & Fixes #8](#8-minikube-keeps-running-the-old-image-after-rebuild).

### Local Docker Network Test (optional, before k8s)

```bash
docker network create three-tier-net
docker network connect three-tier-net local-postgres

docker run -d --name local-backend --network three-tier-net \
  --network-alias backend-service \
  -e DATABASE_URL=postgresql://appuser:Password@local-postgres:5432/appdb \
  -p 8000:8000 castromeka/three-tier-backend:latest

docker run -d --name local-frontend --network three-tier-net \
  -p 8081:80 castromeka/three-tier-frontend:latest
```
Visit `http://localhost:8081`. The `--network-alias backend-service` simulates the k8s Service DNS name that `nginx.conf` expects.

---

## 6 Kubernetes Deployment

### Layout
```
k8s/
├── namespace.yaml
├── postgres/
│   ├── configmap.yaml
│   ├── secret-plain.yaml      (gitignored — real credentials)
│   ├── sealed-secret.yaml      (committed — encrypted)
│   ├── pvc.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── backend/
│   ├── configmap.yaml
│   ├── secret-plain.yaml      (gitignored)
│   ├── sealed-secret.yaml      (committed)
│   ├── deployment.yaml
│   └── service.yaml
└── frontend/
    ├── deployment.yaml
    └── service.yaml
```

### Prerequisites
```bash
minikube start
brew install kubeseal
```

### Step-by-step

```bash
# 1. Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Sealed Secrets controller (one-time per cluster)
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.1/controller.yaml
kubectl get pods -n kube-system | grep sealed-secrets   # wait for Running

# 3. Seal the secrets (secret-plain.yaml -> sealed-secret.yaml)
kubeseal --format yaml --controller-namespace=kube-system \
  < k8s/postgres/secret-plain.yaml > k8s/postgres/sealed-secret.yaml

kubeseal --format yaml --controller-namespace=kube-system \
  < k8s/backend/secret-plain.yaml > k8s/backend/sealed-secret.yaml

# 4. Postgres
kubectl apply -f k8s/postgres/configmap.yaml
kubectl apply -f k8s/postgres/sealed-secret.yaml
kubectl apply -f k8s/postgres/pvc.yaml
kubectl apply -f k8s/postgres/deployment.yaml
kubectl apply -f k8s/postgres/service.yaml

# 5. Backend
kubectl apply -f k8s/backend/configmap.yaml
kubectl apply -f k8s/backend/sealed-secret.yaml
kubectl apply -f k8s/backend/deployment.yaml
kubectl apply -f k8s/backend/service.yaml

# 6. Frontend
kubectl apply -f k8s/frontend/deployment.yaml
kubectl apply -f k8s/frontend/service.yaml
```

### Verify
```bash
kubectl get pods -n three-tier-app
kubectl get secret backend-secret -n three-tier-app -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

### Access the app
With the minikube **docker driver**, the NodePort IP (`192.168.49.2:30080`) isn't directly reachable from the host browser. Use:
```bash
minikube service frontend-service -n three-tier-app
```
This opens a tunneled `http://127.0.0.1:<port>` URL in your browser.

---

## 4. Secrets — Critical Rule

`k8s/*/secret-plain.yaml` and `backend/.env` / `frontend/.env` are gitignored. **Both Postgres-related secrets must use the same password**:
- `postgres-secret.POSTGRES_PASSWORD`
- `backend-secret.DATABASE_URL` (embedded password)

A mismatch causes `FATAL: password authentication failed` at runtime.

To generate a real JWT secret:
```bash
head -c 32 /dev/urandom | base64
```

---

## 7 Errors & Fixes Log

### 1. `psycopg2.OperationalError: Connection refused` (port 5432)
**Cause:** `local-postgres` container not running.
**Fix:** `docker start local-postgres` (or recreate it — see Section 1).

### 2. `FATAL: password authentication failed for user "..."`
**Cause:** Postgres only sets the user/password on **first init** of its data volume. Recreating the container with new `-e POSTGRES_PASSWORD` env vars doesn't change an already-initialized volume; or `.env` and the running container's credentials simply don't match.
**Fix:**
```bash
docker rm -f -v local-postgres   # -v removes the data volume too
docker run -d --name local-postgres -e POSTGRES_USER=... -e POSTGRES_PASSWORD=... -e POSTGRES_DB=appdb -p 5432:5432 postgres:15-alpine
```
Make sure the credentials match `backend/.env`'s `DATABASE_URL`.

### 3. `Import "dotenv" could not be resolved`
**Cause:** `python-dotenv` added to `requirements.txt` but not yet installed in the venv.
**Fix:** `pip install -r requirements.txt` (with venv activated).

### 4. `502 Bad Gateway` on `localhost:8080`
**Cause:** A Homebrew-installed nginx was already running natively on macOS, occupying port 8080 — completely unrelated to the project. The Docker frontend container never started because the port was taken.
**Fix:** Run the frontend container on a different host port (`-p 8081:80`) instead of fighting the existing nginx.

### 5. `ImagePullBackOff`
**Cause:** `k8s/*/deployment.yaml` had `image: three-tier-backend:latest` / `three-tier-frontend:latest` — no DockerHub namespace, so Kubernetes tried (and failed) to pull `docker.io/library/three-tier-backend`.
**Fix:** Update to `castromeka/three-tier-backend:latest` / `castromeka/three-tier-frontend:latest`, matching the images actually pushed to DockerHub.

### 6. `CreateContainerConfigError`
**Cause:** Deployment's `envFrom` referenced a ConfigMap (`backend-config`) and/or Secret (`backend-secret`) that didn't exist yet in the namespace — they were never `kubectl apply`'d.
**Fix:**
```bash
kubectl apply -f k8s/backend/configmap.yaml
kubectl apply -f k8s/backend/sealed-secret.yaml
```

### 7. `CrashLoopBackOff` — `ImportError: email-validator is not installed`
**Cause:** `schemas.py` uses Pydantic's `EmailStr`, which requires the `email-validator` package — missing from `requirements.txt`.
**Fix:** Add `email-validator>=2.0.0` to `backend/requirements.txt`, rebuild the image.

### 8. minikube keeps running the old image after rebuild
**Cause:** `imagePullPolicy: IfNotPresent` + reusing the `:latest` tag means minikube's cached image (same name:tag) is never refreshed, even after `docker push` + `minikube image load`.
**Fix:** Use a **versioned tag** (`:v2`, `:v3`, ...) for every rebuild:
```bash
docker build -t castromeka/three-tier-backend:v2 ./backend
docker push castromeka/three-tier-backend:v2
minikube image load castromeka/three-tier-backend:v2
# update deployment.yaml image: castromeka/three-tier-backend:v2
kubectl apply -f k8s/backend/deployment.yaml
```

### 9. Browser: `192.168.49.2:30080 — ERR_CONNECTION_TIMED_OUT`
**Cause:** minikube's `docker` driver runs the cluster inside an isolated Docker network; the minikube IP isn't routable directly from the macOS host browser.
**Fix:**
```bash
minikube service frontend-service -n three-tier-app
```
Use the tunneled `127.0.0.1:<port>` URL it prints/opens.

### 10. "Signup failed" — no request ever reaches the backend
**Cause:** `frontend/.env` (`VITE_API_URL=http://localhost:8000`, for local dev) was copied into the Docker build context via `COPY . .` and got **baked into the production JS bundle** by Vite at build time (`baseURL: "http://localhost:8000"`). In the browser, `localhost:8000` points to the user's own machine — request never leaves the browser successfully.
**Fix:** Add `frontend/.dockerignore` excluding `.env`, rebuild/push/load a new tag. The bundle then falls back to `baseURL: "/api"`, correctly proxied by nginx to `backend-service:8000`.
