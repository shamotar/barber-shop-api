#!/bin/sh

pip install -r requirements.txt

export PYTHONPATH=/app

alembic upgrade head

cd src

uvicorn main:app --host 0.0.0.0 --port 8000 --reload