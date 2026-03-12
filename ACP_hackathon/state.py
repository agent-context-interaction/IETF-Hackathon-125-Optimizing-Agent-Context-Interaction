from typing import TypedDict, Dict, Any


class ACPState(TypedDict):
    task_results: Dict[str, Any]
    current_agent: str
    retry_count: int
    eval_decision: str