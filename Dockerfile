# ---- 构建阶段 ----
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装 poetry
RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --only=main --no-interaction --no-ansi

# ---- 运行阶段 ----
FROM python:3.12-slim

WORKDIR /app

# 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 复制项目文件
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini ./

EXPOSE 8000

# 启动时先执行迁移，再启动应用
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
