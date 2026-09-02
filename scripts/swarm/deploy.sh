#!/usr/bin/env bash
set -euo pipefail

export DB_NAME="rmit_store"
export DB_USER="rmit"
export DB_PASSWORD="nhaibob1234"
export SECRET_KEY="rmit-store-production-super-secure-key-$(date +%s)"

echo "==> Deploying stack $STACK_NAME..."
docker stack deploy -c orchestration/docker-stack.yml "$STACK_NAME" --with-registry-auth

echo "==> Waiting for backend to be ready..."
attempt=1
while true; do
    if curl -s http://localhost:8000/healthz/ >/dev/null; then
        echo "   Backend is up!"
        break
    elif [ "$attempt" -eq 12 ]; then
        echo "   Backend failed to start after 2 minutes" >&2
        echo "========================================================"
        echo "   [DEBUG] IN LOG CỦA BACKEND ĐỂ TÌM LỖI:"
        echo "========================================================"
        docker service logs ${STACK_NAME}_backend --raw
        exit 1
    else
        echo "   Backend not ready yet (attempt ${attempt}/12), retrying in 10s..."
        sleep 10
        attempt=$((attempt+1))
    fi
done

echo "==> Running migrations..."
BACKEND_CONTAINER=$(docker ps -q -f name=${STACK_NAME}_backend | head -n 1)
if [ -n "$BACKEND_CONTAINER" ]; then
    docker exec "$BACKEND_CONTAINER" python manage.py migrate
else
    echo "Không tìm thấy container backend để chạy migrate!"
    exit 1
fi

echo "==> Stack state"
docker stack services "$STACK_NAME"
echo
echo "Store:    http://localhost/            (or the node's public IP)"
echo "Health:   http://localhost:8000/healthz/   http://localhost:8000/readyz/"
echo "Version:  http://localhost:8000/api/version/"
