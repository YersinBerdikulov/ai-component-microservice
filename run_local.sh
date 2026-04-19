#!/bin/bash
set -e

if [ ! -d "venv" ]; then
  python -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example — fill in your API keys before running."
  exit 1
fi

uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
