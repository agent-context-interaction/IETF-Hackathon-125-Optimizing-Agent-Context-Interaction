
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from agents import run_sub_agent
from config import client
from evaluator import evaluate_by_master
from metrics import add_usage, reset_run_stats

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
        "task_description": "Based on sub1 data, analyze cost control and operational efficiency of four companies, about 200 words per company.",
        "dependencies": ["G1"],
    },
    {
        "goal_id": "G4",
        "agent": "sub4",
        "task_description": "Synthesize sub2 and sub3 outputs, form key conclusions of four companies, about 300 words per company.",
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
    return {
        '''
        To be devised
        '''
    }


def build_agent_context(goal: Dict[str, Any], dep_agents: List[str], task_context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""
You are the main agent's task decomposition module. Please generate AgentContext for the specified sub-agent based on the latest TaskContext.



Rules:
to be devised

Only output strict JSON (only AgentContext object):
to be devised
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    add_usage(getattr(response, "usage", None))







state: Dict[str, Any] = {
    "task_results": {},
    "agent_contexts": {},
    "current_agent": "",
}

task_context = build_task_context()
print(f"[run] ENABLE_EVAL={ENABLE_EVAL}")
reset_run_stats()

while True:
    "devise the logic to determine which agent to run next based on the current state and task context"
    break


sub8_output = state["task_results"].get("sub8", "")
if sub8_output:
    print("\n===== final sub8 output =====")
    print(sub8_output)

print("\n===== task context =====")
print(task_context)

print("\n===== run metrics =====")
print(f"prompt_tokens: ")
print(f"completion_tokens: ")
print(f"total_tokens: ")
elapsed = []
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
    f.write(f"prompt_tokens: \n")
    f.write(f"completion_tokens: \n")
    f.write(f"total_tokens: \n")
    f.write(f"elapsed_seconds: {elapsed_text}\n")

print(f"saved_report: {output_file}")