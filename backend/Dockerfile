# ---- 编译阶段：安装所有依赖 ----
FROM python:3.11-slim AS builder

WORKDIR /app

# 只安装编译时需要的工具
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 把依赖安装到独立目录，供后面阶段复制
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- 运行阶段：只复制必要文件 ----
FROM python:3.11-slim

# 仅安装运行时的 libpq（psycopg 需要）
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从编译阶段复制已安装好的包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
