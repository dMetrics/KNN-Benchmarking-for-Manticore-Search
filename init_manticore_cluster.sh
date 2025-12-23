#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.yml"

echo "[+] Starting Manticore cluster containers..."
docker compose -f "$COMPOSE_FILE" down
docker compose -f "$COMPOSE_FILE" up -d

wait_for_port() {
  local port="$1"
  local name="$2"

  echo "[+] Waiting for $name on port $port..."
  while ! nc -z 127.0.0.1 "$port" >/dev/null 2>&1; do
    sleep 1
  done
  echo "[+] $name is up on port $port"
}

# 1) Wait for MySQL ports on all three nodes (host ports)
wait_for_port 9306 "mc-1"
wait_for_port 9316 "mc-2"
wait_for_port 9326 "mc-3"

echo "[+] Creating cluster FTS_1 on node 1 (mc-1)..."
# Run mysql INSIDE the mc-1 container
docker exec mc-1 mysql -P9306 -e "CREATE CLUSTER FTS_1;" \
  || echo "[!] CREATE CLUSTER failed (probably already exists) – continuing"

echo "[+] Joining node 2 (mc-2) to cluster..."
docker exec mc-2 mysql -P9306 -e "JOIN CLUSTER FTS_1 AT 'mc-1:9312';"

echo "[+] Joining node 3 (mc-3) to cluster..."
docker exec mc-3 mysql -P9306 -e "JOIN CLUSTER FTS_1 AT 'mc-1:9312';"

echo "[✅] Cluster FTS_1 initialization complete."
