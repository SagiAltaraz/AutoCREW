from typing import Optional, TypedDict


class AgentState(TypedDict):
    task_id: str
    input_task: str
    manager_plan: str
    research_results: str
    analysis_results: str
    final_output: str
    current_agent: str
    agent_statuses: dict  # {agent_name: 'waiting'|'running'|'done'|'error'}
    error: Optional[str]
    metadata: dict  # tokens_used, durations
