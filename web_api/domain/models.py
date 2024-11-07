from pydantic import BaseModel, field_validator

from common.domain.models import TaskStatus


class TaskPayload(BaseModel):
    payload: str

    @field_validator("payload")
    def payload_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError("Payload cannot be empty or whitespace")
        return value

class TaskResponse(BaseModel):
    task_id: int
    status: TaskStatus
