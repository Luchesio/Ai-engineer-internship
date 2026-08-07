#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — add your OPENAI_API_KEY, or set MOCK=1 to run without one."
fi

set -a
source .env
set +a

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

if ! python3 -c "import fastapi, uvicorn, langchain_openai" 2>/dev/null; then
  echo "Installing dependencies..."
  python3 -m pip install -q -r requirements.txt
fi

if [ "${MOCK:-0}" != "1" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is not set. Either set it in .env or run: MOCK=1 ./run.sh"
  exit 1
fi

echo "Starting on http://${HOST}:${PORT}  (docs at /docs, health at /healthz)"
exec python3 -m uvicorn main:app --host "$HOST" --port "$PORT" --reload