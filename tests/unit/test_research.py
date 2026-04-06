import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.research_agent import research_node
from agents.state import AgentState


def _state_with_plan(base: AgentState) -> AgentState:
    return AgentState(**{**base, "manager_plan": "1. What is AWS?\n2. What is GCP?"})


@pytest.mark.asyncio
async def test_research_returns_results(sample_agent_state):
    state = _state_with_plan(sample_agent_state)

    mock_executor = MagicMock()
    mock_executor.ainvoke = AsyncMock(return_value={"output": "Research findings here"})

    with patch("agents.research_agent.AgentExecutor", return_value=mock_executor):
        with patch("agents.research_agent.create_react_agent", return_value=MagicMock()):
            result = await research_node(state)

    assert result["research_results"] == "Research findings here"
    assert result["agent_statuses"]["research"] == "done"
    assert result["error"] is None


@pytest.mark.asyncio
async def test_research_uses_rag_context(sample_agent_state):
    state = _state_with_plan(sample_agent_state)

    mock_similar = [
        {"input_task": "Compare AWS vs GCP", "output_preview": "AWS leads in..."},
    ]

    mock_executor = MagicMock()
    mock_executor.ainvoke = AsyncMock(return_value={"output": "Research with RAG"})

    with patch("agents.research_agent.AgentExecutor", return_value=mock_executor):
        with patch("agents.research_agent.create_react_agent", return_value=MagicMock()):
            with patch("agents.tools.memory.search_similar", return_value=mock_similar):
                result = await research_node(state)

    assert result["agent_statuses"]["research"] == "done"


@pytest.mark.asyncio
async def test_research_handles_empty_rag(sample_agent_state):
    state = _state_with_plan(sample_agent_state)

    mock_executor = MagicMock()
    mock_executor.ainvoke = AsyncMock(return_value={"output": "Research without RAG"})

    with patch("agents.research_agent.AgentExecutor", return_value=mock_executor):
        with patch("agents.research_agent.create_react_agent", return_value=MagicMock()):
            with patch("agents.tools.memory.search_similar", return_value=[]):
                result = await research_node(state)

    assert result["research_results"] == "Research without RAG"
    assert result["error"] is None
