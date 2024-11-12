from fastapi import FastAPI

from web_api.exception_handler import apply_exception_handler
from web_api.routers.tasks import task_router


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(task_router)

    apply_exception_handler(app=app)

    return app
