# ---------- Stage 1: build frontend ----------
FROM node:20-slim AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build    # erzeugt /app/dist

# ---------- Stage 2: python runtime ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-Dependencies
COPY middleware/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code
COPY middleware/ ./middleware/

# Frontend-Build aus Stage 1 -> /app/static
COPY --from=frontend-build /app/dist /app/static

# Defaults (im Compose heißt der Broker "mosquitto")
ENV BROKER_HOST=mosquitto \
    BROKER_PORT=1883 \
    STATIC_DIR=/app/static \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080

EXPOSE 8080
CMD ["python", "-u", "middleware/middleware.py"]
