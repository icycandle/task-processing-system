from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

from common.domain.models import TaskStatus

Base = declarative_base()


class TaskORM(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payload = Column(String, nullable=False)
    status = Column(String, default=TaskStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
