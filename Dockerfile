# build stage 
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# runtime image 
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
WORKDIR /app
COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY . .
CMD ["sh", "scripts/start.sh"]
