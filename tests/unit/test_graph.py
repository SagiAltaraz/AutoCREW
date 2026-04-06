import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.state import AgentState


def _make_mock_node(name: str, output_field: str, output_value: str):
    async def node(state: AgentState) -> dict:
        statuses = dict(state.get("agent_statuses", {}))
        statuses[name] = "done"
        return {
            output_field: output_value,
            "current_agent": name,
            "agent_statuses": statuses,
            "metadata": {},
            "error": None,
        }
    return node


@pytest.mark.asyncio
async def test_full_pipeline_runs():
    with patch("agents.graph.manager_node", _make_mock_node("manager", "manager_plan", "Plan")):
        with patch("agents.graph.research_node", _make_mock_node("research", "research_results", "Research")):
            with patch("agents.graph.analyst_node", _make_mock_node("analyst", "analysis_results", "Analysis")):
                with patch("agents.graph.writer_node", _make_mock_node("writer", "final_output", "Final report")):
                    with patch("agents.graph.crew") as mock_crew:
                        mock_crew.astream = AsyncMock(return_value=_fake_stream())

                        with patch("redis.asyncio.from_url"):
                            from agents.graph import run_crew
                            result = await run_crew("test-123", "Test topic")

    assert isinstance(result, dict)


async def _fake_stream():
    agents = [
        ("manager", {"manager_plan": "Plan", "current_agent": "manager",
                     "agent_statuses": {"manager": "done", "research": "waiting", "analyst": "waiting", "writer": "waiting"},
                     "metadata": {}, "error": None}),
        ("research", {"research_results": "Research", "current_agent": "research",
                      "agent_statuses": {"manager": "done", "research": "done", "analyst": "waiting", "writer": "waiting"},
                      "metadata": {}, "error": None}),
        ("analyst", {"analysis_results": "Analysis", "current_agent": "analyst",
                     "agent_statuses": {"manager": "done", "research": "done", "analyst": "done", "writer": "waiting"},
                     "metadata": {}, "error": None}),
        ("writer", {"final_output": "Final report", "current_agent": "writer",
                    "agent_statuses": {"manager": "done", "research": "done", "analyst": "done", "writer": "done"},
                    "metadata": {"total_tokens": 400}, "error": None}),
    ]
    for name, state in agents:
        yield {name: state}


@pytest.mark.asyncio
async def test_pipeline_state_flow():
    from agents.state import AgentState

    state: AgentState = {
        "task_id": "abc",
        "input_task": "Test",
        "manager_plan": "",
        "research_results": "",
        "analysis_results": "",
        "final_output": "",
        "current_agent": "",
        "agent_statuses": {"manager": "waiting", "research": "waiting", "analyst": "waiting", "writer": "waiting"},
        "error": None,
        "metadata": {},
    }

    manager_result = await _make_mock_node("manager", "manager_plan", "Plan")(state)
    assert manager_result["manager_plan"] == "Plan"
    assert manager_result["agent_statuses"]["manager"] == "done"

    merged = {**state, **manager_result}
    research_result = await _make_mock_node("research", "research_results", "Research")(merged)
    assert research_result["research_results"] == "Research"
