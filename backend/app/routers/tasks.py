import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.db.postgres import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_AGENT_NAMES = ["manager", "research", "analyst", "writer"]
_AGENT_OUTPUT_FIELDS = {
    "manager": "manager_plan",
    "research": "research_results",
    "analyst": "analysis_results",
    "writer": "final_output",
}


class CreateTaskRequest(BaseModel):
    input_text: str


def _get_agent_output(state: dict, agent_name: str) -> str:
    return state.get(_AGENT_OUTPUT_FIELDS.get(agent_name, ""), "") or ""


async def _run_task(task_id: str, input_text: str) -> None:
    """Background task — runs the agent crew and updates DB on completion."""
    try:
        from agents.graph import run_crew
        from data.kafka_producer import AutoCrewProducer

        producer = AutoCrewProducer()
        final_state = await run_crew(task_id, input_text)
        metadata = final_state.get("metadata", {})
        statuses = final_state.get("agent_statuses", {})

        async with get_db() as conn:
            if final_state.get("error"):
                await conn.execute(
                    "UPDATE tasks SET status='failed', completed_at=$1 WHERE id=$2",
                    datetime.now(timezone.utc),
                    uuid.UUID(task_id),
                )
            else:
                await conn.execute(
                    "UPDATE tasks SET status='completed', completed_at=$1 WHERE id=$2",
                    datetime.now(timezone.utc),
                    uuid.UUID(task_id),
                )
                await conn.execute(
                    "INSERT INTO results (id, task_id, content, created_at) VALUES ($1, $2, $3, $4)",
                    uuid.uuid4(),
                    uuid.UUID(task_id),
                    final_state.get("final_output", ""),
                    datetime.now(timezone.utc),
                )

            for agent_name in _AGENT_NAMES:
                await conn.execute(
                    """INSERT INTO agent_runs
                       (id, task_id, agent_name, status, started_at, completed_at, duration_ms, tokens_used, output)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    uuid.uuid4(),
                    uuid.UUID(task_id),
                    agent_name,
                    statuses.get(agent_name, "done"),
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    metadata.get(f"{agent_name}_duration_ms", 0),
                    metadata.get(f"{agent_name}_tokens", 0),
                    _get_agent_output(final_state, agent_name),
                )
                producer.publish_agent_completed(
                    task_id=task_id,
                    agent_name=agent_name,
                    tokens_used=metadata.get(f"{agent_name}_tokens", 0),
                    duration_ms=metadata.get(f"{agent_name}_duration_ms", 0),
                )

        producer.publish_task_completed(
            task_id=task_id,
            total_tokens=metadata.get("total_tokens", 0),
            total_duration_ms=sum(
                metadata.get(f"{a}_duration_ms", 0) for a in _AGENT_NAMES
            ),
        )

    except Exception:
        try:
            async with get_db() as conn:
                await conn.execute(
                    "UPDATE tasks SET status='failed', completed_at=$1 WHERE id=$2",
                    datetime.now(timezone.utc),
                    uuid.UUID(task_id),
                )
        except Exception:
            pass


@router.post("")
async def create_task(body: CreateTaskRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    if not body.input_text.strip():
        raise HTTPException(status_code=400, detail="input_text cannot be empty")

    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    async with get_db() as conn:
        await conn.execute(
            "INSERT INTO tasks (id, input_text, status, created_at) VALUES ($1, $2, $3, $4)",
            uuid.UUID(task_id),
            body.input_text,
            "pending",
            now,
        )

    try:
        from data.kafka_producer import AutoCrewProducer
        AutoCrewProducer().publish_task_created(task_id=task_id, input_text=body.input_text)
    except Exception:
        pass

    background_tasks.add_task(_run_task, task_id, body.input_text)
    return {"task_id": task_id, "status": "pending", "created_at": now.isoformat()}


@router.get("/{task_id}")
async def get_task(task_id: str) -> dict[str, Any]:
    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task_id")

    async with get_db() as conn:
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id=$1", uid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        agent_runs = await conn.fetch(
            "SELECT * FROM agent_runs WHERE task_id=$1 ORDER BY started_at", uid
        )
        result = await conn.fetchrow(
            "SELECT content FROM results WHERE task_id=$1 ORDER BY created_at DESC LIMIT 1", uid
        )

    return {
        "id": str(task["id"]),
        "input_text": task["input_text"],
        "status": task["status"],
        "created_at": task["created_at"].isoformat() if task["created_at"] else None,
        "completed_at": task["completed_at"].isoformat() if task["completed_at"] else None,
        "agent_runs": [
            {
                "agent_name": r["agent_name"],
                "status": r["status"],
                "duration_ms": r["duration_ms"],
                "tokens_used": r["tokens_used"],
                "output": r["output"],
            }
            for r in agent_runs
        ],
        "result": result["content"] if result else None,
    }


@router.get("")
async def list_tasks() -> list[dict[str, Any]]:
    async with get_db() as conn:
        tasks = await conn.fetch(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 20"
        )
    return [
        {
            "id": str(t["id"]),
            "input_text": t["input_text"],
            "status": t["status"],
            "created_at": t["created_at"].isoformat() if t["created_at"] else None,
            "completed_at": t["completed_at"].isoformat() if t["completed_at"] else None,
        }
        for t in tasks
    ]
