import json
import os
from typing import Optional

from kafka import KafkaProducer as _KafkaProducer

from data.schemas.task_event import TaskCreatedEvent, AgentCompletedEvent, TaskCompletedEvent

_producer: Optional[_KafkaProducer] = None


def _get_producer() -> _KafkaProducer:
    global _producer
    if _producer is None:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        _producer = _KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer


class AutoCrewProducer:
    def publish_task_created(self, task_id: str, input_text: str, user_id: Optional[str] = None) -> None:
        event = TaskCreatedEvent(task_id=task_id, input_text=input_text, user_id=user_id)
        try:
            _get_producer().send("task.created", event.model_dump())
        except Exception:
            pass

    def publish_agent_completed(self, task_id: str, agent_name: str, tokens_used: int, duration_ms: int) -> None:
        event = AgentCompletedEvent(
            task_id=task_id,
            agent_name=agent_name,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
        try:
            _get_producer().send("agent.completed", event.model_dump())
        except Exception:
            pass

    def publish_task_completed(self, task_id: str, total_tokens: int, total_duration_ms: int) -> None:
        event = TaskCompletedEvent(
            task_id=task_id,
            total_tokens=total_tokens,
            total_duration_ms=total_duration_ms,
        )
        try:
            _get_producer().send("task.completed", event.model_dump())
        except Exception:
            pass
