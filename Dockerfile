# CaseSentinel — single Cloud Run container: FastAPI serving the built dashboard.
# Stage 1: build the React dashboard.
FROM node:24-slim AS web
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# Stage 2: Python API + agents, serving the built static bundle.
FROM python:3.12-slim AS api
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORE_BACKEND=firestore \
    WEB_DIST_DIR=/app/web/dist
WORKDIR /app

COPY apps/api/pyproject.toml apps/api/README.md* ./apps/api/
COPY apps/api/src ./apps/api/src
RUN pip install "./apps/api[firestore]"

# Built dashboard from stage 1.
COPY --from=web /web/dist ./web/dist

# Cloud Run provides $PORT.
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn casesentinel.api.app:app --host 0.0.0.0 --port ${PORT}"]
