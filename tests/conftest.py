import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_env():
    # 設置測試環境的環境變量
    os.environ["RABBITMQ_URL"] = "amqp://guest:guest@localhost:5672/"
    yield
    # 清理環境變量
    os.environ.pop("RABBITMQ_URL", None)
