"""
Evaluation Module

Responsible for evaluating and deciding on sub-agent outputs by the main agent.
Main features:
- Parse AgentContext output by sub-agents
- Evaluate task completion based on ItemstateUpdates and KeyInformation
- Decide whether to pass, retry, or force pass
- Provide feedback for corrections
"""

import json
import re
from typing import Any, Dict

from config import client
from metrics import add_usage

MAX_RETRY = 2



def _build_eval_payload(agent_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'to be devised'
    }


def evaluate_by_master(agent_context: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
    eval_payload = _build_eval_payload(agent_context)
    prompt = f"""
You are the main agent's evaluation module. Please evaluate whether the sub-agent completed the task based on the following structured content.
Evaluation input: to be devised


Requirements:
1. Only judge whether task is satisfied based on ItemstateUpdates, KeyInformation.
2. Do not rely on or assume any additional context.
3. decision value can only be "pass", "retry", "force_pass".
Please output strict JSON:
{{
  "decision": "pass" or "retry" or "force_pass",
  "feedback": "if retry needed, give concise actionable correction suggestions; otherwise can be empty"
}}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    add_usage(getattr(response, "usage", None))
    raw = (response.choices[0].message.content or "").strip()


    if decision not in {"pass", "retry", "force_pass"}:
        decision = "retry"
        if not feedback:
            feedback = raw

    next_retry = retry_count
    if decision == "retry":
        next_retry = retry_count + 1
        if next_retry >= MAX_RETRY:
            decision = "force_pass"

    if decision == "pass":
        next_retry = 0

    return {
        "decision": decision,
        "feedback": feedback,
        "retry_count": next_retry,
        "raw_eval": raw,
    }