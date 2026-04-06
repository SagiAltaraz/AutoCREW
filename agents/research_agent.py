import time
from typing import Any

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks.base import BaseCallbackHandler

from agents.state import AgentState
from agents.tools.search import web_search


class _TokenCounter(BaseCallbackHandler):
    """Counts tokens across all LLM calls in an AgentExecutor run."""

    def __init__(self) -> None:
        self.total_tokens = 0

    def on_llm_end(self, response: Any, **_: Any) -> None:
        for gen_list in response.generations:
            for gen in gen_list:
                usage = getattr(gen.message, "usage_metadata", None) or {}
                self.total_tokens += usage.get("total_tokens", 0)


REACT_PROMPT = PromptTemplate.from_template("""You are a Research Agent. You MUST use web_search to find current information — do NOT answer from memory.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: I need to search for this using web_search
Action: the action to take, should be one of [{tool_names}]
Action Input: specific search query
Observation: the result of the action
... (repeat for EACH sub-question in the research plan)
Thought: I now have enough information
Final Answer: comprehensive research findings covering all sub-questions

Begin!

Question: {input}
Thought:{agent_scratchpad}""")

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
tools = [web_search]


async def research_node(state: AgentState) -> dict[str, Any]:
    """Gather comprehensive research using web search for each sub-question."""
    start_time = time.time()

    statuses = dict(state.get("agent_statuses", {}))
    statuses["research"] = "running"
    metadata = dict(state.get("metadata", {}))

    try:
        rag_context = ""
        try:
            from agents.tools.memory import search_similar
            similar = search_similar(state["input_task"])
            if similar:
                previews = "\n".join(
                    f"- [{r['input_task'][:60]}]: {r['output_preview'][:150]}"
                    for r in similar
                )
                rag_context = f"CONTEXT FROM PAST RESEARCH:\n{previews}\nUse if relevant."
        except Exception:
            pass

        token_counter = _TokenCounter()
        agent = create_react_agent(llm, tools, REACT_PROMPT)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=12,
            handle_parsing_errors=True,
            callbacks=[token_counter],
        )

        research_query = (
            f"Research the following topic: {state['input_task']}\n\n"
            f"Research plan:\n{state['manager_plan']}\n\n"
            f"Use web_search for EACH sub-question. Provide detailed findings."
        )
        if rag_context:
            research_query += f"\n\n{rag_context}"

        result = await executor.ainvoke({"input": research_query})
        research_results = result.get("output", "")

        metadata["research_tokens"] = token_counter.total_tokens
        metadata["research_duration_ms"] = int((time.time() - start_time) * 1000)
        metadata.setdefault("total_tokens", 0)
        metadata["total_tokens"] += token_counter.total_tokens
        statuses["research"] = "done"

        return {
            "research_results": research_results,
            "current_agent": "research",
            "agent_statuses": statuses,
            "metadata": metadata,
            "error": None,
        }

    except Exception as e:
        statuses["research"] = "error"
        metadata["research_duration_ms"] = int((time.time() - start_time) * 1000)
        return {
            "current_agent": "research",
            "agent_statuses": statuses,
            "metadata": metadata,
            "error": str(e),
        }
