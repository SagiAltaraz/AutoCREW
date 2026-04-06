from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreatedEvent(BaseModel):
    event_type: str = "task.created"
    version: str = "1.0"
    task_id: str
    input_text: str
    user_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentCompletedEvent(BaseModel):
    event_type: str = "agent.completed"
    version: str = "1.0"
    task_id: str
    agent_name: str
    tokens_used: int = 0
    duration_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskCompletedEvent(BaseModel):
    event_type: str = "task.completed"
    version: str = "1.0"
    task_id: str
    total_tokens: int = 0
    total_duration_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
