import json
from typing import Any, Dict, List, Optional
from .templating import render_template
from .reactor import ReActAgent
from .llm import LLMAdapter
import asyncio


class WorkflowRunner:
    def __init__(self, llm: LLMAdapter, tools: Dict[str, Any] = None):
        self.llm = llm
        self.tools = tools or {}

    async def run(self, workflow: Dict[str, Any], event_queue: Optional[asyncio.Queue] = None) -> Dict[str, Any]:
        """Run the workflow. If `event_queue` is provided, emit events as dicts for each step and nested ReAct events.

        Emitted events (examples):
        - {"type": "step_start", "step_id": id}
        - {"type": "step_end", "step_id": id, "parsed": ...}
        - ReAct events are forwarded from the agent (thought/action/observation/final)
        """
        memory = {}
        inputs = workflow.get("entry_inputs", {})
        memory.update(inputs)
        steps: List[Dict[str, Any]] = workflow.get("steps", [])

        for step in steps:
            step_id = step.get("id")
            if event_queue is not None:
                await event_queue.put({"type": "step_start", "step_id": step_id, "name": step.get("name")})

            tmpl = step.get("template", "")
            parser = step.get("parser", "text")
            ctx = {"memory": memory, "inputs": inputs}
            rendered = render_template(tmpl, ctx)

            resp = await self.llm.generate(rendered)
            text = resp.get("text", "")

            if parser == "json":
                try:
                    parsed = json.loads(text)
                except Exception:
                    parsed = {"_raw": text}
            elif parser == "react":
                # Spawn a ReAct agent and forward its iteration events
                agent = ReActAgent(self.llm, self.tools)
                parsed_agent = await agent.run(rendered, event_queue=event_queue)
                parsed = {"react_result": parsed_agent}
            else:
                parsed = {"_raw": text}

            # store outputs
            outputs = step.get("outputs", [])
            if outputs:
                if len(outputs) == 1:
                    memory[outputs[0]] = parsed
                else:
                    # attempt to map by keys
                    if isinstance(parsed, dict):
                        for k in outputs:
                            memory[k] = parsed.get(k)
                    else:
                        # fallback
                        memory[outputs[0]] = parsed

            if event_queue is not None:
                await event_queue.put({"type": "step_end", "step_id": step_id, "parsed": parsed})

        return {"memory": memory}
