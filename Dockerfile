FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN set -eux; \
    find /app/app/scripts -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; ; \
    chmod +x /app/app/scripts/*.sh
