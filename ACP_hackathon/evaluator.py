"""
评估模块

负责主智能体对子智能体输出结果的评估和决策。
主要功能：
- 解析子智能体输出的AgentContext
- 根据ItemstateUpdates和KeyInformation评估任务完成度
- 决定是否通过、重试或强制通过
- 提供反馈意见用于修正
"""

import json
import re
from typing import Any, Dict

from config import client
from metrics import add_usage

MAX_RETRY = 2


def _extract_json_object(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if not text:
        return {}

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        try:
            data = json.loads(fenced.group(1))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return {}
    return {}


def _build_eval_payload(agent_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ItemstateUpdates": agent_context.get("ItemstateUpdates", []),
        "KeyInformation": agent_context.get("KeyInformation", []),
    }


def evaluate_by_master(agent_context: Dict[str, Any], retry_count: int) -> Dict[str, Any]:
    eval_payload = _build_eval_payload(agent_context)
    prompt = f"""
You are the main agent's evaluation module. Please evaluate whether the sub-agent completed the task based on the following structured content.
Evaluation input:
{json.dumps(eval_payload, ensure_ascii=False, separators=(",",":"))}

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
    parsed = _extract_json_object(raw)

    decision = str(parsed.get("decision", "")).strip().lower() if parsed else ""
    feedback = str(parsed.get("feedback", "")).strip() if parsed else raw

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