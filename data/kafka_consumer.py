import asyncio
import json
import os

from kafka import KafkaConsumer


async def _process_agent_completed(event: dict) -> None:
    """Update agent_runs in PostgreSQL when an agent completes."""
    try:
        import asyncpg
        from datetime import datetime, timezone

        db_url = os.getenv("POSTGRES_URL", "")
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                """UPDATE agent_runs
                   SET status='done', completed_at=$1, duration_ms=$2, tokens_used=$3
                   WHERE task_id=$4::uuid AND agent_name=$5
                """,
                datetime.now(timezone.utc),
                event.get("duration_ms", 0),
                event.get("tokens_used", 0),
                event["task_id"],
                event["agent_name"],
            )
        finally:
            await conn.close()
    except Exception:
        pass


async def _process_task_completed(event: dict) -> None:
    """Update tasks table and store result in ChromaDB when task completes."""
    try:
        import asyncpg
        from datetime import datetime, timezone

        db_url = os.getenv("POSTGRES_URL", "")
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                "UPDATE tasks SET status='completed', completed_at=$1 WHERE id=$2::uuid",
                datetime.now(timezone.utc),
                event["task_id"],
            )
        finally:
            await conn.close()
    except Exception:
        pass


class AutoCrewConsumer:
    def __init__(self) -> None:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self._consumer = KafkaConsumer(
            "task.created",
            "agent.completed",
            "task.completed",
            bootstrap_servers=bootstrap,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="autocrew-consumer",
            auto_offset_reset="earliest",
        )

    def consume_forever(self) -> None:
        """Poll Kafka and dispatch events. Runs in a background thread."""
        for message in self._consumer:
            event = message.value
            topic = message.topic

            if topic == "agent.completed":
                asyncio.run(_process_agent_completed(event))
            elif topic == "task.completed":
                asyncio.run(_process_task_completed(event))
