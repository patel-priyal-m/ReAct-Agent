from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path
import json
import asyncio

from src.agent_demo.llm import MockLLM, OpenAIAdapter
import uuid

# In-memory registry for running tasks: run_id -> { task, queue }
TASK_REGISTRY: dict = {}
from src.agent_demo.workflow import WorkflowRunner
from src.agent_demo import tools as tools_mod

app = FastAPI(title="Agent Demo API")

# Allow local dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def load_example_workflow(name: str = "hybrid_workflow.json") -> dict:
    p = Path(__file__).parent.parent / "examples" / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run-workflow")
async def run_workflow(use_openai: bool = False):
    """Run the example hybrid workflow and return the final memory object.

    Query param `use_openai=true` will attempt to use the OpenAIAdapter (requires OPENAI_API_KEY env var).
    """
    workflow = load_example_workflow()
    if use_openai:
        llm = OpenAIAdapter()
    else:
        llm = MockLLM()

    tools = {"search": tools_mod.search_tool, "run_tests": tools_mod.run_tests_tool}
    runner = WorkflowRunner(llm, tools=tools)
    result = await runner.run(workflow)
    return result


@app.get("/stream-workflow")
async def stream_workflow(request: Request):
    """Stream workflow execution as server-sent events (SSE).

    Connect with EventSource from the browser to receive events.
    """
    workflow = load_example_workflow()
    llm = MockLLM()
    tools = {"search": tools_mod.search_tool, "run_tests": tools_mod.run_tests_tool}
    runner = WorkflowRunner(llm, tools=tools)

    run_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()

    async def producer():
        try:
            # announce start
            await queue.put({"type": "started", "run_id": run_id})
            result = await runner.run(workflow, event_queue=queue)
            # final message containing result
            await queue.put({"type": "done", "result": result})
        except asyncio.CancelledError:
            # push cancelled event
            await queue.put({"type": "cancelled", "run_id": run_id})
        except Exception as e:
            await queue.put({"type": "error", "error": str(e)})
        finally:
            # cleanup registry
            TASK_REGISTRY.pop(run_id, None)

    task = asyncio.create_task(producer())
    # register task and queue
    TASK_REGISTRY[run_id] = {"task": task, "queue": queue}

    async def event_generator():
        # Yield events from the queue as SSE
        while True:
            # If client disconnected, stop producing
            if await request.is_disconnected():
                # optionally cancel the task when client disconnects
                # task.cancel()
                break
            try:
                ev = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            data = json.dumps(ev, default=str)
            yield f"data: {data}\n\n"
            if ev.get("type") in ("done", "error", "cancelled"):
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")



@app.post("/cancel/{run_id}")
async def cancel_run(run_id: str):
    """Cancel a running workflow by run_id. Returns 404 if not found."""
    entry = TASK_REGISTRY.get(run_id)
    if not entry:
        return {"status": "not_found"}
    task = entry.get("task")
    queue = entry.get("queue")
    # cancel task
    task.cancel()
    # notify client via queue
    try:
        await queue.put({"type": "cancel_requested", "run_id": run_id})
    except Exception:
        pass
    return {"status": "cancelled", "run_id": run_id}
