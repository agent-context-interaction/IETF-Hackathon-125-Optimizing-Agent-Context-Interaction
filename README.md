# IETF Hackathon Project: Optimizing Agent Context Interactions

This repository contains two runnable versions: `baseline` (PlainText Context) and `ACP_hackathon` (Structured Context). Participants should build on the `ACP_hackathon` version to highlight the advantages of the protocol-based approach.

**Project Info**

Multi-agent collaboration has been widely studied as an effective approach for addressing complex and multi-turn interactive tasks. However, in current agentic workflows, contextual information is often exchanged in an unstructured and redundant manner, leading to excessive token consumption, increased execution latency, and reduced task completion success rates, especially in multi-step and multi-agent scenarios. The project focuses on designing and experimenting with structured agent context interaction mechanisms, including precise context distribution, context isolation among agents, and fine-grained task and progress management. A master–invoked agent interaction scheme is expected to demonstrate how task-related contexts can be selectively delivered to invoked agents and incrementally updated during task execution.

**Project Structure**
- `baseline/`: Baseline version (PlainText Context)
- `ACP_hackathon/`: ACP protocol version (Structured Context)
- `requirements.txt`: Shared dependencies
- `generate_dashboard.py`: Performance comparison report generator
- `comparison_dashboard.html`: Example report output

**Run the Baseline Project**

Prerequisites: Python 3.10+ installed.

1. Create and activate a virtual environment

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure API key (recommended)
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="YOUR_KEY"

# macOS / Linux
export DEEPSEEK_API_KEY="YOUR_KEY"
```

4. Run the Baseline version
```bash
python baseline/main.py
```

**How to contribute**

Please develop inside `ACP_hackathon/` and keep `baseline/` unchanged for fair comparison.

1. Fork this repository and create a new branch
2. Prepare the environment and install dependencies as above
3. Run the ACP version to verify it works
```bash
python ACP_hackathon/main.py
```
4. Implement improvements in `ACP_hackathon/`
Focus files: `ACP_hackathon/agents.py`, `ACP_hackathon/evaluator.py`, `ACP_hackathon/metrics.py`, `ACP_hackathon/state.py`
5. Submit a PR
Briefly describe your improvements, assumptions, and comparison results

**Suggested Additions (Optional)**
- Add clearer context structures or protocol fields
- Improve multi-agent collaboration and error recovery
- Add new evaluation metrics or comparison dimensions

**Performance Comparison Report (Optional)**
After generating run reports in both `baseline/` and `ACP_hackathon/` (format `YYYYMMDD_HHMMSS.txt`), run:
```bash
python generate_dashboard.py
```
This script generates `comparison_dashboard.html` and attempts to open it in your browser.

**FAQ**
- If you encounter certificate or network issues, check proxy settings or adjust `httpx` settings in `config.py`.
- If you have any suggestions/questions or just show your interest in this topic, you can send an email to changzeze@huawei.com.

