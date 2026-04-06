import time
from typing import Any

from langchain_openai import ChatOpenAI

from agents.state import AgentState

SYSTEM_PROMPT = """You are an Analyst Agent. Your job is to extract meaningful insights from raw research data.

Analyze the research findings and produce:

## KEY INSIGHTS
- [3-5 most important insights]

## PATTERNS & TRENDS
- [Patterns you observe in the data]

## RISKS & CHALLENGES
- [Key risks or challenges identified]

## OPPORTUNITIES
- [Opportunities or positive developments]

## DATA POINTS
- [Important statistics, numbers, or facts]

Be analytical, objective, and evidence-based. Back every claim with data from the research."""

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)


async def analyst_node(state: AgentState) -> dict[str, Any]:
    """Extract key insights, patterns, risks, and opportunities from research."""
    start_time = time.time()

    statuses = dict(state.get("agent_statuses", {}))
    statuses["analyst"] = "running"
    metadata = dict(state.get("metadata", {}))

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Original task: {state['input_task']}\n\n"
                    f"Research findings:\n{state['research_results']}"
                ),
            },
        ]

        response = await llm.ainvoke(messages)
        analysis = response.content

        tokens = response.usage_metadata or {}
        metadata["analyst_tokens"] = tokens.get("total_tokens", 0)
        metadata["analyst_duration_ms"] = int((time.time() - start_time) * 1000)
        metadata.setdefault("total_tokens", 0)
        metadata["total_tokens"] += metadata["analyst_tokens"]

        statuses["analyst"] = "done"

        return {
            "analysis_results": analysis,
            "current_agent": "analyst",
            "agent_statuses": statuses,
            "metadata": metadata,
            "error": None,
        }

    except Exception as e:
        statuses["analyst"] = "error"
        return {
            "current_agent": "analyst",
            "agent_statuses": statuses,
            "metadata": metadata,
            "error": str(e),
        }
