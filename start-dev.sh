#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> 检查 PostgreSQL..."
if ! docker ps --format '{{.Names}}' | grep -q brandshow_db_dev; then
  echo "==> 启动 PostgreSQL 容器..."
  docker run -d --name brandshow_db_dev \
    -e POSTGRES_DB=brandshow \
    -e POSTGRES_USER=brandshow \
    -e POSTGRES_PASSWORD=brandshow123 \
    -p 5433:5432 \
    postgres:16-alpine
  echo "==> 等待数据库就绪..."
  until docker exec brandshow_db_dev pg_isready -U brandshow >/dev/null 2>&1; do sleep 1; done
fi
echo "    PostgreSQL OK"

echo "==> 运行数据库迁移..."
cd "$ROOT/backend"
.venv/bin/alembic upgrade head

echo "==> 启动后端 (port 8000)..."
ENVIRONMENT=production .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "==> 启动前端 (port 5173)..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
