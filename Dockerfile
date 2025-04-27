
    FROM python:3.12-slim AS base
    ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
    WORKDIR /app
    

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    

    COPY . .
    CMD ["sh", "scripts/start.sh"]
    