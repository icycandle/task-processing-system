from datetime import datetime
from enum import Enum

from loguru import logger
from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class OperationNotAllowed(Exception):
    message: str


class Task(BaseModel):
    id: int | None = Field(None)
    payload: str = Field(..., min_length=1)
    status: TaskStatus = Field(TaskStatus.PENDING)

    created_at: datetime | None = Field(None)

    @field_validator("payload")
    def validate_payload(cls, v):
        if not v.strip():
            raise ValueError("Payload cannot be empty or whitespace")
        return v

    def mark_processing(self):
        if self.status != TaskStatus.PENDING:
            logger.warning(f"Task status {self.status} cannot be processed")
            raise OperationNotAllowed(f"Task status {self.status} cannot be processed")
        self.status = TaskStatus.PROCESSING

    def mark_completed(self):
        if self.status != TaskStatus.PROCESSING:
            logger.warning(f"Task status {self.status} cannot be processed")
            raise OperationNotAllowed(f"Task status {self.status} cannot be processed")
        self.status = TaskStatus.COMPLETED

    def cancel(self):
        if self.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            logger.warning(f"Task status {self.status} cannot be processed")
            raise OperationNotAllowed(f"Task status {self.status} cannot be processed")
        self.status = TaskStatus.CANCELED
