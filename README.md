# Hybrid Agent Demo (Template + ReAct)

This repository contains a minimal Python demo showing how to build two educational agent patterns:

- Template-chained workflows (templating + LLM calls + parser extraction)
- ReAct-style agent (Thought → Action → Observation loop) invoked as a tool from the workflow

This demo runs with a mock LLM by default (no external API keys needed). You can configure an OpenAI API key to try real LLM calls by setting `OPENAI_API_KEY` in a `.env` file.

Quick start (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_demo.py
```

To enable real OpenAI usage, create a `.env` file with:

```
OPENAI_API_KEY=sk-...
```

Then run `python run_demo.py --use-openai` (note: usage will send prompts to OpenAI).

Frontend (React) UI
--------------------
A minimal React UI is included under the `web/` folder. It calls the backend `POST /run-workflow` endpoint.

To run the backend server:

```powershell
pip install -r requirements.txt
uvicorn src.server:app --host 127.0.0.1 --port 8000
```

To run the React UI (requires Node.js):

```powershell
cd web
npm install
npm run dev
```

Open the UI at `http://localhost:5173` and click "Run Workflow" to execute the demo and view results.

Project layout (key files):
- `src/agent_demo/llm.py` — LLM adapter (Mock + optional OpenAI)
- `src/agent_demo/templating.py` — Jinja2 wrapper for step templating
- `src/agent_demo/reactor.py` — ReAct agent controller and loop
- `src/agent_demo/workflow.py` — Workflow runner (template-chain orchestration)
- `examples/hybrid_workflow.json` — example hybrid workflow
- `run_demo.py` — launch the workflow with the mock LLM
- `tests/test_agent.py` — smoke tests (pytest)

This demo is intentionally small and focused on patterns; extend with more tools, robust parsers, and real LLM adapters for production use.
