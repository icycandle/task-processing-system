# Task Processing System

## Project Structure

- **common/**：包含共享的 domain model、 repo 和 infra。
- **web_api/**：提供任務建立和取消的 Web API。
- **consumer/**：任務消費者，處理訊息佇列中的任務。
- **tests/**：包含端對端（E2E）測試。
- **migrations/**： database migration file, 使用 alembic。
- **Dockerfile**：用於建立 Docker 映像。
- **docker-compose.yml**：用於啟動整個系統的 Docker Compose 配置。

## Install and Run

1. **Run docker compose**

```bash
docker-compose up --build
```

2. **Run e2e test**

```bash
pytest tests/e2e/test_e2e.py
```
