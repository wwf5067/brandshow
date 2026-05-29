#!/usr/bin/env bash
# brandshow Lighthouse 服务器一次性初始化脚本
# 用法（在 Lighthouse 服务器上）:
#   scp deploy/bootstrap.sh ubuntu@<IP>:/tmp/
#   ssh ubuntu@<IP> 'bash /tmp/bootstrap.sh'
#
# 前提：newsfeed 项目已部署，postgres 容器已运行

set -euo pipefail

APP_DIR=/opt/brandshow
NEWSFEED_DIR=/opt/newsfeed

echo "==> Checking newsfeed postgres is running..."
if ! docker inspect newsfeed-postgres-1 >/dev/null 2>&1 && \
   ! docker inspect newsfeed_postgres_1 >/dev/null 2>&1; then
  echo "WARNING: newsfeed postgres container not found."
  echo "Make sure newsfeed is deployed first."
fi

echo "==> Creating brandshow database in newsfeed postgres..."
# 获取 newsfeed postgres 的实际容器名
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E '^newsfeed[_-]postgres' | head -1 || echo "")

if [ -n "$PG_CONTAINER" ]; then
  # 读取 newsfeed 的 postgres 超级用户密码
  NEWSFEED_ENV="$NEWSFEED_DIR/.env"
  if [ -f "$NEWSFEED_ENV" ]; then
    POSTGRES_SUPERUSER_PASS=$(grep '^POSTGRES_PASSWORD=' "$NEWSFEED_ENV" | cut -d= -f2 || echo "")
  fi

  # 创建 brandshow 用户和数据库（幂等）
  docker exec "$PG_CONTAINER" psql -U newsfeed -c \
    "DO \$\$ BEGIN
       IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'brandshow') THEN
         CREATE ROLE brandshow WITH LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
       END IF;
     END \$\$;" || echo ">> User creation skipped (may already exist)"

  docker exec "$PG_CONTAINER" psql -U newsfeed -c \
    "CREATE DATABASE brandshow OWNER brandshow;" 2>/dev/null || \
    echo ">> Database brandshow already exists, skipping."

  echo ">> Database ready. Remember to update POSTGRES_PASSWORD in $APP_DIR/.env"
else
  echo "WARNING: Could not find newsfeed postgres container."
  echo "Please manually create the brandshow database:"
  echo "  docker exec <postgres_container> psql -U postgres -c \"CREATE DATABASE brandshow;\""
fi

echo "==> Preparing $APP_DIR"
sudo mkdir -p "$APP_DIR"
sudo chown "$USER":"$USER" "$APP_DIR"

echo "==> Opening firewall port 8090..."
sudo ufw allow 8090/tcp || true

if [ ! -f "$APP_DIR/.env" ]; then
  cat > "$APP_DIR/.env" <<'ENV'
# brandshow 生产配置，填好后从 GitHub Actions 触发部署

BACKEND_IMAGE=ghcr.io/YOUR_GITHUB_USERNAME/brandshow-backend:latest

POSTGRES_USER=brandshow
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
POSTGRES_DB=brandshow

ENVIRONMENT=production
CORS_ORIGINS=*
ENV
  echo ">> Created $APP_DIR/.env (template)"
  echo ">> 请编辑 $APP_DIR/.env，修改 YOUR_GITHUB_USERNAME 和数据库密码"
else
  echo ">> $APP_DIR/.env already exists, leaving untouched."
fi

echo ""
echo "==> Done! 接下来："
echo "   1) vim $APP_DIR/.env           # 填入 GitHub 用户名和强密码"
echo "   2) 在 GitHub 仓库配置 Secrets:"
echo "      SSH_HOST=$( curl -s ifconfig.me 2>/dev/null || echo '<服务器IP>' )"
echo "      SSH_USER=$USER"
echo "      SSH_PORT=22"
echo "      SSH_KEY=<你的 ed25519 私钥>"
echo "   3) push main 分支触发自动部署"
echo "   4) 部署后访问: http://<服务器IP>:8090"
