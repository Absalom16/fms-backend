FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Development stage — hot reload via Flask dev server
FROM base AS development
ENV FLASK_ENV=development
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]

# Production stage — Gunicorn with 4 workers
FROM base AS production
RUN pip install --no-cache-dir gunicorn
RUN chmod +x /app/docker-entrypoint.sh
EXPOSE 5000
CMD ["/app/docker-entrypoint.sh"]
