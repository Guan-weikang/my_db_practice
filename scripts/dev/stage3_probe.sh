#!/usr/bin/env bash
set -euo pipefail

BACK_PID=""
FRONT_PID=""

cleanup() {
  if [ -n "${BACK_PID}" ]; then
    kill "${BACK_PID}" >/dev/null 2>&1 || true
  fi
  if [ -n "${FRONT_PID}" ]; then
    kill "${FRONT_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

(cd /home/mochen/db_practice/backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/stage3-backend-probe.log 2>&1) &
BACK_PID=$!

(cd /home/mochen/db_practice/frontend && npm run dev -- --host 127.0.0.1 --port 4173 >/tmp/stage3-frontend-probe.log 2>&1) &
FRONT_PID=$!

sleep 6

PROXY_ENV=(env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY)

"${PROXY_ENV[@]}" curl --noproxy '*' -sS http://127.0.0.1:8000/api/v1/health/
printf '\n---\n'

"${PROXY_ENV[@]}" curl --noproxy '*' -sS -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"stage3_viewer","password":"Password123"}'
printf '\n---\n'

TOKEN=$("${PROXY_ENV[@]}" curl --noproxy '*' -sS -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"stage3_viewer","password":"Password123"}' | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

"${PROXY_ENV[@]}" curl --noproxy '*' -sS http://127.0.0.1:8000/api/v1/family-trees \
  -H "Authorization: Bearer ${TOKEN}"
printf '\n---\n'

"${PROXY_ENV[@]}" curl --noproxy '*' -sS http://127.0.0.1:8000/api/v1/family-trees/32 \
  -H "Authorization: Bearer ${TOKEN}"
printf '\n---\n'

"${PROXY_ENV[@]}" curl --noproxy '*' -I -sS http://127.0.0.1:4173
