import json
import re
from typing import Any, Dict, List

from config import client
from metrics import add_usage

MODEL = "deepseek-chat"

SUB_AGENT_CAPABILITIES = {
    "sub1": "Responsible for collecting latest key financial data of Chinese new energy vehicle companies, no analysis.",
    "sub2": "Responsible for profitability and gross margin structure analysis of new energy vehicle companies.",
    "sub3": "Responsible for cost control and operational efficiency analysis of new energy vehicle companies.",
    "sub4": "Responsible for integrating sub2 and sub3, output key conclusions.",
    "sub5": "Responsible for collecting broker ratings, stock price performance, expert opinions of new energy vehicle companies.",
    "sub6": "Responsible for collecting new energy vehicle policy information and summarizing impacts.",
    "sub7": "Responsible for comprehensive risk assessment based on financial, market, and policy of new energy vehicle companies.",
    "sub8": "Responsible for synthesizing conclusions and risks, providing investment recommendations and rankings.",
}


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


def _build_dependency_context(state: Dict[str, Any], dependencies: List[str]) -> str:
    if not dependencies:
        return "None"

    task_results = state.get("task_results", {})
    agent_contexts = state.get("agent_contexts", {})
    blocks = []
    for dep in dependencies:
        full_output = str(task_results.get(dep, "")).strip()
        if not full_output:
            ctx = agent_contexts.get(dep, {})
            full_output = str(ctx.get("full_output", "")).strip()
        if full_output:
            blocks.append(f"[{dep} full output]\n{full_output}")
    return "\n\n".join(blocks) if blocks else "None"





def call_llm_stream_full_output(prompt: str, agent_name: str) -> str:
    print(f"\n===== {agent_name} stream =====")
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a financial analysis sub-agent. Only output the final content that meets user requirements."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        stream=True,
        stream_options={"include_usage": True},
    )

    parts: List[str] = []
    for chunk in stream:
        usage = getattr(chunk, "usage", None)
        if usage:
            add_usage(usage)

        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue

        delta = getattr(choices[0], "delta", None)
        text = getattr(delta, "content", None) if delta else None
        if text:
            print(text, end="", flush=True)
            parts.append(text)

    print(f"\n===== {agent_name} stream end =====\n")
    return "".join(parts).strip()

def _normalize_agent_context(parsed: Dict[str, Any], base_context: Dict[str, Any]) -> Dict[str, Any]:
    "to be devised"
    return

def run_sub_agent(state: Dict[str, Any], agent_context: Dict[str, Any], feedback: str = "") -> Dict[str, Any]:
    agent_name = agent_context.get("AgentName", "sub_agent")
    state["current_agent"] = agent_name

    capability = SUB_AGENT_CAPABILITIES.get(agent_name, "General Analysis and Output")
    dependencies = agent_context.get("Dependencies", [])
    dep_context = _build_dependency_context(state, dependencies)
    todo_items = agent_context.get("todoItems", [])
    todo_text = "\n".join(
        [f"- {item.get('itemId', '')}: {item.get('description', '')}" for item in todo_items]
    ) or "- None"

    prompt = f"""
You are {agent_name}. Capability boundary: {capability}

Consider full task output:
{dep_context}

Please complete sub-tasks based on todoItems, task list as follows:
{todo_text}

If there is evaluation feedback, must correct:
{feedback if feedback else "None"}

Please only output strict JSON (only AgentContext object, no extra text):
{{
"to be devised"
}}

Rules:
to be devised
"""


    raw_output = call_llm_stream_full_output(prompt, agent_name)
    parsed = _extract_json_object(raw_output)
    updated_context = _normalize_agent_context(parsed, agent_context)   
    if not updated_context.get("full_output"):
        updated_context["full_output"] = raw_output

    state["task_results"][agent_name] = updated_context["full_output"]
    state["agent_contexts"][agent_name] = updated_context
    return {
        "agent_context": updated_context,
        "full_output": updated_context["full_output"],
        "raw": raw_output,
    }