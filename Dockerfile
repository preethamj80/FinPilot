# Build the React app first, then include only its production bundle in FastAPI.
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements_backend.txt ./
RUN python -m pip install --no-cache-dir -r requirements_backend.txt

COPY backend/ ./backend/
COPY src/ ./src/
COPY ml_models.py utils.py ./
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

EXPOSE 10000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
