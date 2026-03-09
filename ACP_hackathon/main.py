"""
主程序模块

负责新能源车企投资分析任务的编排和执行。
主要功能：
- 定义8个分析目标及其依赖关系
- 构建任务上下文和智能体上下文
- 按依赖顺序调度子智能体执行
- 管理全局状态和任务结果
- 生成最终报告和性能指标
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from agents import run_sub_agent
from config import client
from evaluator import evaluate_by_master
from metrics import add_usage, finish_run_stats, get_run_stats, reset_run_stats

ENABLE_EVAL = True
COMPANIES = ["NIO", "Li Auto", "XPeng", "BYD"]

GOALS: List[Dict[str, Any]] = [
    {
        "goal_id": "G1",
        "agent": "sub1",
        "task_description": "Collect key financial data of NIO, Li Auto, XPeng, BYD (revenue scale, gross margin, delivery volume, R&D investment, cash reserves), no analysis, structured output.",
        "dependencies": [],
    },
    {
        "goal_id": "G2",
        "agent": "sub2",
        "task_description": "Based on sub1 data, analyze profitability and gross margin structure of four companies, about 200 words per company.",
        "dependencies": ["G1"],
    },
    {
        "goal_id": "G3",
        "agent": "sub3",
        "task_description": "Based on sub1 data, analyze cost control and operational efficiency of four companies, about 300 words per company.",
        "dependencies": ["G1"],
    },
    {
        "goal_id": "G4",
        "agent": "sub4",
        "task_description": "Synthesize sub2 and sub3 outputs, form key conclusions of four companies, about 400 words per company.",
        "dependencies": ["G2", "G3"],
    },
    {
        "goal_id": "G5",
        "agent": "sub5",
        "task_description": "Collect broker ratings, stock price performance, expert strategic evaluations from 2024Q4 to January 2026, summarize by company structure, about 300 words per company.",
        "dependencies": [],
    },
    {
        "goal_id": "G6",
        "agent": "sub6",
        "task_description": "Collect new energy vehicle policy related news from 2024Q4 to January 2026, and summarize policy environment changes and industry impacts.",
        "dependencies": [],
    },
    {
        "goal_id": "G7",
        "agent": "sub7",
        "task_description": "Synthesize sub1, sub5, sub6, output risk assessment of four companies, about 200 words per company.",
        "dependencies": ["G1", "G5", "G6"],
    },
    {
        "goal_id": "G8",
        "agent": "sub8",
        "task_description": "Synthesize sub4 and sub7, provide investment recommendations and investment rankings of four companies, total words not less than 400.",
        "dependencies": ["G4", "G7"],
    },
]


def build_task_context() -> Dict[str, Any]:
    """构建任务上下文"""
    return {
        "TaskContext": {
            "TaskID": "T1",
            "TaskName": "New Energy Vehicle Company Investment Analysis",
            "TaskDescription": "Complete financial, operational, policy, risk and investment conclusion analysis through 8 steps.",
            "GoalStatus": [{"Goal": goal["goal_id"], "Status": "Not Started"} for goal in GOALS],
        }
    }


def _extract_json_object(raw: str) -> Dict[str, Any]:
    """从文本中提取JSON对象"""
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


def _fallback_agent_context(goal: Dict[str, Any], dep_agents: List[str]) -> Dict[str, Any]:
    """生成默认的AgentContext"""
    todo_items = []
    item_state_updates = []
    key_information = []

    for idx, company in enumerate(COMPANIES, start=1):
        item_id = f"{goal['goal_id']}_item_{idx}"
        todo_items.append(
            {
                "itemId": item_id,
                "description": f"Only for {company}: {goal['task_description']}",
            }
        )
        item_state_updates.append({"itemId": item_id, "state": 0})
        key_information.append({"itemId": item_id, "outputabstract": ""})

    return {
        "AgentID": goal["goal_id"],
        "AgentName": goal["agent"],
        "SubTaskID": goal["goal_id"],
        "Dependencies": dep_agents,
        "todoItems": todo_items,
        "ItemstateUpdates": item_state_updates,
        "KeyInformation": key_information,
        "full_output": "",
    }


def _normalize_generated_agent_context(
    generated: Dict[str, Any], goal: Dict[str, Any], dep_agents: List[str]
) -> Dict[str, Any]:
    """规范化AgentContext结构"""
    template = _fallback_agent_context(goal, dep_agents)
    return {
        "AgentID": generated.get("AgentID") or template["AgentID"],
        "AgentName": generated.get("AgentName") or template["AgentName"],
        "SubTaskID": generated.get("SubTaskID") or template["SubTaskID"],
        "Dependencies": generated.get("Dependencies")
        if isinstance(generated.get("Dependencies"), list)
        else template["Dependencies"],
        "todoItems": generated.get("todoItems")
        if isinstance(generated.get("todoItems"), list) and generated.get("todoItems")
        else template["todoItems"],
        "ItemstateUpdates": generated.get("ItemstateUpdates")
        if isinstance(generated.get("ItemstateUpdates"), list)
        else template["ItemstateUpdates"],
        "KeyInformation": generated.get("KeyInformation")
        if isinstance(generated.get("KeyInformation"), list)
        else template["KeyInformation"],
        "full_output": str(generated.get("full_output") or ""),
    }


def build_agent_context(goal: Dict[str, Any], dep_agents: List[str], task_context: Dict[str, Any]) -> Dict[str, Any]:
    """通过LLM构建AgentContext"""
    prompt = f"""
You are the main agent's task decomposition module. Please generate AgentContext for the specified sub-agent based on the latest TaskContext.

Latest TaskContext:
{json.dumps(task_context, ensure_ascii=False, separators=(",",":"))}

Current Goal:
{json.dumps(goal, ensure_ascii=False, separators=(",",":"))}

Available company list:
{json.dumps(COMPANIES, ensure_ascii=False)}

Rules:
1. If task description is strongly related to companies, split todoItems by company (usually one item per company).
2. If task description does not depend on company dimension, split items by task logic yourself, quantity determined by task complexity, keep it minimal, do not split by company when generating investment recommendations.
3. ItemstateUpdates must align with todoItems item by item and initial state=0.
4. KeyInformation must align with todoItems item by item and outputabstract is empty string.
5. Dependencies use the following values, do not modify:
{json.dumps(dep_agents, ensure_ascii=False)}

Only output strict JSON (only AgentContext object):
{{
  "AgentID": "{goal['goal_id']}",
  "AgentName": "{goal['agent']}",
  "SubTaskID": "{goal['goal_id']}",
  "Dependencies": [],
  "todoItems": [{{"itemId": "...", "description": "..."}}],
  "ItemstateUpdates": [{{"itemId": "...", "state": 0}}],
  "KeyInformation": [{{"itemId": "...", "outputabstract": ""}}],
  "full_output": ""
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
    normalized = _normalize_generated_agent_context(parsed, goal, dep_agents)
    return normalized


def get_finished_goals(task_context: Dict[str, Any]) -> Set[str]:
    """获取已完成的目标ID集合"""
    goal_status = task_context["TaskContext"].get("GoalStatus", [])
    return {item.get("Goal", "") for item in goal_status if item.get("Status") == "Finished"}


def set_goal_finished(task_context: Dict[str, Any], goal_id: str) -> None:
    """标记目标为已完成"""
    goal_status = task_context["TaskContext"].get("GoalStatus", [])
    for item in goal_status:
        if item.get("Goal") == goal_id:
            item["Status"] = "Finished"
            return


def select_next_goal(task_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """选择下一个可执行的目标"""
    finished = get_finished_goals(task_context)
    for goal in GOALS:
        if goal["goal_id"] in finished:
            continue
        deps = goal.get("dependencies", [])
        if all(dep in finished for dep in deps):
            return goal
    return None


def resolve_dependency_agents(goal: Dict[str, Any]) -> List[str]:
    """解析目标依赖的智能体名称"""
    dep_goal_ids = goal.get("dependencies", [])
    dep_agents = []
    for dep_goal in GOALS:
        if dep_goal["goal_id"] in dep_goal_ids:
            dep_agents.append(dep_goal["agent"])
    return dep_agents


state: Dict[str, Any] = {
    "task_results": {},
    "agent_contexts": {},
    "current_agent": "",
}

task_context = build_task_context()
print(f"[run] ENABLE_EVAL={ENABLE_EVAL}")
reset_run_stats()

while True:
    next_goal = select_next_goal(task_context)
    if next_goal is None:
        break

    goal_id = next_goal["goal_id"]
    agent_name = next_goal["agent"]
    dep_agents = resolve_dependency_agents(next_goal)
    agent_context = state["agent_contexts"].get(agent_name)
    if not agent_context:
        agent_context = build_agent_context(next_goal, dep_agents, task_context)

    retry_count = 0
    feedback = ""

    while True:
        result = run_sub_agent(
            state=state,
            agent_context=agent_context,
            feedback=feedback,
        )
        updated_agent_context = result["agent_context"]
        agent_context = updated_agent_context
        state["agent_contexts"][agent_name] = agent_context

        if not ENABLE_EVAL:
            set_goal_finished(task_context, goal_id)
            break

        eval_result = evaluate_by_master(
            agent_context=updated_agent_context,
            retry_count=retry_count,
        )
        retry_count = eval_result["retry_count"]

        print(
            f"[master-eval] goal={goal_id}, agent={agent_name}, decision={eval_result['decision']}, retry_count={retry_count}"
        )

        if eval_result["decision"] in {"pass", "force_pass"}:
            set_goal_finished(task_context, goal_id)
            break

        feedback = eval_result["feedback"]

finish_run_stats()
stats = get_run_stats()

sub8_output = state["task_results"].get("sub8", "")
if sub8_output:
    print("\n===== final sub8 output =====")
    print(sub8_output)

print("\n===== task context =====")
print(task_context)

print("\n===== run metrics =====")
print(f"prompt_tokens: {stats['prompt_tokens']}")
print(f"completion_tokens: {stats['completion_tokens']}")
print(f"total_tokens: {stats['total_tokens']}")
elapsed = stats["elapsed_seconds"]
print(f"elapsed_seconds: {elapsed:.2f}" if isinstance(elapsed, float) else "elapsed_seconds: N/A")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"{timestamp}.txt"
elapsed_text = f"{elapsed:.2f}" if isinstance(elapsed, float) else "N/A"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("===== final sub8 output =====\n")
    f.write(sub8_output if sub8_output else "(empty)\n")
    f.write("\n===== task context =====\n")
    f.write(f"{task_context}\n")
    f.write("\n===== run metrics =====\n")
    f.write(f"prompt_tokens: {stats['prompt_tokens']}\n")
    f.write(f"completion_tokens: {stats['completion_tokens']}\n")
    f.write(f"total_tokens: {stats['total_tokens']}\n")
    f.write(f"elapsed_seconds: {elapsed_text}\n")

print(f"saved_report: {output_file}")