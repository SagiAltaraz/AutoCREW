import json
import os
import time
from typing import Any

from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.manager_agent import manager_node
from agents.research_agent import research_node
from agents.analyst_agent import analyst_node
from agents.writer_agent import writer_node


def build_graph() -> Any:
    graph = StateGraph(AgentState)

    graph.add_node("manager", manager_node)
    graph.add_node("research", research_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("writer", writer_node)

    graph.add_edge(START, "manager")
    graph.add_edge("manager", "research")
    graph.add_edge("research", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


crew = build_graph()

_AGENT_OUTPUT_FIELDS = {
    "manager": "manager_plan",
    "research": "research_results",
    "analyst": "analysis_results",
    "writer": "final_output",
}

_AGENT_ORDER = ["manager", "research", "analyst", "writer"]


async def run_crew(task_id: str, input_task: str) -> AgentState:
    """Run the full agent pipeline and publish real-time events via Redis."""
    import redis.asyncio as aioredis

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    channel = f"task:{task_id}"

    initial_state: AgentState = {
        "task_id": task_id,
        "input_task": input_task,
        "manager_plan": "",
        "research_results": "",
        "analysis_results": "",
        "final_output": "",
        "current_agent": "",
        "agent_statuses": {
            "manager": "waiting",
            "research": "waiting",
            "analyst": "waiting",
            "writer": "waiting",
        },
        "error": None,
        "metadata": {},
    }

    start_time = time.time()
    final_state: AgentState = initial_state

    async with aioredis.from_url(redis_url) as redis:
        async for chunk in crew.astream(initial_state):
            for agent_name, state_update in chunk.items():
                if agent_name not in _AGENT_ORDER:
                    continue

                final_state = {**final_state, **state_update}

                statuses = final_state.get("agent_statuses", {})
                metadata = final_state.get("metadata", {})

                output_text = final_state.get(_AGENT_OUTPUT_FIELDS.get(agent_name, ""), "") or ""

                await redis.publish(channel, json.dumps({
                    "type": "agent_update",
                    "agent": agent_name,
                    "status": statuses.get(agent_name, "done"),
                    "timestamp": time.time(),
                    "tokens_used": metadata.get(f"{agent_name}_tokens", 0),
                    "duration_ms": metadata.get(f"{agent_name}_duration_ms", 0),
                    "preview": output_text[:200],
                }))

        total_ms = int((time.time() - start_time) * 1000)

        await redis.publish(channel, json.dumps({
            "type": "task_complete",
            "output": final_state.get("final_output", ""),
            "duration_ms": total_ms,
            "total_tokens": final_state.get("metadata", {}).get("total_tokens", 0),
        }))

    try:
        from agents.tools.memory import store_result
        store_result(task_id, input_task, final_state.get("final_output", ""))
    except Exception:
        pass

    return final_state
