# Task Processing System

## Project Structure

```
.
├── common/   <- 整個 domain 共享的程式，遵循 clean-architecture 的原則。
│   ├── applications/
│   │   └── use_case/ <- 只依賴 domain & interface 的關鍵商業邏輯 
│   │       ├── consumer/
│   │       │   └── task_processing.py
│   │       └── web_api/
│   │           └── task_create.py
│   ├── constants.py <- 整個專案共用的變數可以放這裡
│   ├── domain/ <- TaskEntity & 所有 interface 宣告在此 
│   │   ├── models.py
│   │   ├── repo/
│   │   │   └── task_repo.py
│   │   └── services/
│   │       ├── consume_queue_service.py
│   │       ├── prometheus_service.py
│   │       ├── send_to_queue_service.py
│   │       └── task_cancellation_cache.py
│   └── infrastructure/ <- 各種與底層細節相關的邏輯實作，interface 的實作
│       ├── database.py
│       ├── db_schema.py
│       ├── dependencies.py
│       ├── repo/
│       │   └── task_repo.py
│       └── services/
│           ├── consume_queue_service.py
│           ├── prometheus_service.py
│           ├── send_to_queue_service.py
│           └── task_cancellation_cache.py
├── consumer/ <- queue consumer 的 fastapi entry point 
│   └── main.py
├── web_api/ <- web_api 的 fastapi entry point
│   ├── domain/ <- web API 的 DTO schema  
│   │   └── models.py
│   └── main.py
├── tests/ <- 為了管理方便， test 檔案路徑會一一對應測試對象的專案路徑
│   ├── common/
│   │   └── applications/
│   │       └── use_case/
│   │           ├── consumer/
│   │           │   └── test_task_processing.py
│   │           └── web_api/
│   │               └── test_task_create.py
│   ├── conftest.py <- pytest fixture
│   ├── e2e/ <- 這裡的測試使用 localhost 透過 http 跟 docker-compose 裡的 service 互動
│   │   └── test_happy_path.py
│   └── performance/ <- 使用說明參看下方
│       └── locustfile.py
├── migrations/ <- database migration file, 使用 alembic。會在 docker-compose up 時順便 apply。
│   ├── env.py
│   ├── script.py.mako
│   ├── versions/
│   │   ├── 24757941f6cc_0001_create_task_table.py
│   │   └── 54430a7a23c1_0002_add_task_timestamp_fields.py
│   └── README
├── grafana-configs/
│   └── ConsumerSuccess-1731396473547.json
├── Dockerfile
├── docker-compose.yml <- 用於啟動整個 dev 環境的 Docker Compose 配置。
├── prometheus.yml
├── rabbitmq.conf
├── pyproject.toml
├── wait-for-it.sh
└── README.md

```

## Install and Run

1. **Run docker compose to turn up Dev System**

```bash
docker-compose up --build
```

2. install poetry on system and run
```bash
poetry install && poetry shell 
```

3. **Run e2e/unit test**

```bash
poetry run pytest
```

## Performance Test

### 進入 Grafana 主頁
1. 開啟瀏覽器並前往 Grafana 頁面，位於 http://localhost:3000
2. 在 Grafana 頁面左側，選擇 Data Sources。 
  - 點擊 Add data source，在列表中選擇 Prometheus。 
  - 在 HTTP URL 欄位中，輸入 Prometheus 的 URL http://prometheus:9090
  - 點擊 Save & Test，確認連接成功。 
3. 新增儀表板
  - 可以 import `grafana/ConsumerSuccess-1731396473547.json`
  - 如果打算手動創建 Dashboard 的內容 ，返回 Grafana 主頁，選擇 Dashboard，然後點擊 Add new panel。
  - 在新面板中，選擇 Query 區域，使用以下 Query 來顯示系統 metrics
    - consumer 消化速度: `rate(tasks_processed_total{status="success"}[1m])`
    - Task life-cycle 平均時間: `rate(task_execution_seconds_sum[1m]) / rate(task_execution_seconds_count[1m])`


### 使用 locust 產生 request
1. 執行 `locust -f tests/performance/locustfile.py --host=http://localhost:8000`
2. 在 http://localhost:8089 觸發 Performance Test, 並在 grafana 中觀看結果


## Assumptions and Design Decisions

- **共用 Dockerfile**:  consumer 跟 web_api 有些許不同的 depends, 但是共用 docker image 可以減少兩者不一致的風險，也加快編譯時間
- **consumer & web_api 的目錄**: 以 clean-architecture 的原則來說，其實放在 `interfaces` 目錄也可以，但名稱容易跟 interface class 搞混，而且 entry-point 藏太深可能對讀 code 的人來說也不直覺。所以選擇在 project_root 開兩個專用 dir。
- **Monitoring**: 使用 Prometheus 記錄 Task 「從 create 到 process complete」 的時間，這對使用者來說是關鍵的 SLA 特徵。
- **效能優化策略**: sleep(3) 較接近低CPU、高IO的性質。所以優化的方向往 async function currency 的方向前進。
- **Cancel 策略**: 使用 redis 作為 Cancel signal 的 cache，雖然 double write 會有不一致的風險，但可以降低 batch_process 中對 database query 的依賴。
- **Message Queue Optimize**: 在 RabbitMQ 的 config 中盡量不使用 disk IO，使 process 重用 connection。
- **Database query 優化策略**: 使用 batch_process 減少 db query 的數量。
- **Test 策略**: 使用 e2e 走最重要的 path。 unit-test 負責各種 edge case。
