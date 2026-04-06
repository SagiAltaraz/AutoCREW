import pytest
from unittest.mock import MagicMock, patch

from data.schemas.task_event import TaskCreatedEvent, AgentCompletedEvent, TaskCompletedEvent


def test_event_schema_task_created():
    event = TaskCreatedEvent(task_id="abc-123", input_text="Research topic")
    assert event.event_type == "task.created"
    assert event.version == "1.0"
    assert event.task_id == "abc-123"
    assert event.timestamp is not None


def test_event_schema_agent_completed():
    event = AgentCompletedEvent(task_id="abc-123", agent_name="manager", tokens_used=50, duration_ms=1200)
    assert event.event_type == "agent.completed"
    assert event.agent_name == "manager"
    assert event.tokens_used == 50


def test_event_schema_task_completed():
    event = TaskCompletedEvent(task_id="abc-123", total_tokens=400, total_duration_ms=5000)
    assert event.event_type == "task.completed"
    assert event.total_tokens == 400


def test_kafka_producer_serializes():
    mock_producer = MagicMock()

    with patch("data.kafka_producer._get_producer", return_value=mock_producer):
        from data.kafka_producer import AutoCrewProducer
        producer = AutoCrewProducer()
        producer.publish_task_created("task-1", "Test input")

    mock_producer.send.assert_called_once()
    topic, payload = mock_producer.send.call_args[0]
    assert topic == "task.created"
    assert payload["task_id"] == "task-1"
    assert payload["event_type"] == "task.created"


def test_kafka_producer_agent_completed_serializes():
    mock_producer = MagicMock()

    with patch("data.kafka_producer._get_producer", return_value=mock_producer):
        from data.kafka_producer import AutoCrewProducer
        producer = AutoCrewProducer()
        producer.publish_agent_completed("task-1", "manager", 100, 1500)

    mock_producer.send.assert_called_once()
    _, payload = mock_producer.send.call_args[0]
    assert payload["agent_name"] == "manager"
    assert payload["tokens_used"] == 100
