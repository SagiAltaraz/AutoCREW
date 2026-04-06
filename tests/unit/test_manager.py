import pytest
from unittest.mock import AsyncMock, patch

from agents.manager_agent import manager_node
from agents.state import AgentState


@pytest.mark.asyncio
async def test_manager_returns_plan(sample_agent_state, mock_openai_response):
    with patch("agents.manager_agent.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_openai_response)

        result = await manager_node(sample_agent_state)

        assert result["manager_plan"] == "Mock LLM output for testing"
        assert result["current_agent"] == "manager"
        assert result["error"] is None


@pytest.mark.asyncio
async def test_manager_updates_status(sample_agent_state, mock_openai_response):
    with patch("agents.manager_agent.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_openai_response)

        result = await manager_node(sample_agent_state)

        assert result["agent_statuses"]["manager"] == "done"


@pytest.mark.asyncio
async def test_manager_tracks_tokens(sample_agent_state, mock_openai_response):
    with patch("agents.manager_agent.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_openai_response)

        result = await manager_node(sample_agent_state)

        assert result["metadata"]["manager_tokens"] == 100
        assert result["metadata"]["total_tokens"] == 100
        assert result["metadata"]["manager_duration_ms"] >= 0


@pytest.mark.asyncio
async def test_manager_handles_error(sample_agent_state):
    with patch("agents.manager_agent.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API error"))

        result = await manager_node(sample_agent_state)

        assert result["agent_statuses"]["manager"] == "error"
        assert "API error" in result["error"]
