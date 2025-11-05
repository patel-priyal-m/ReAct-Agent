import json
import asyncio
from typing import Dict, Any, Callable


class ReActAgent:
    """A lightweight ReAct controller that instructs an LLM to emit JSON with thought/action/action_input.

    The agent expects the LLM to return a JSON string like:
    {"thought": "...", "action": "search", "action_input": {"query":"..."}, "final_answer": null}

    The controller will invoke the matching tool (from tools dict) and feed observation back to the agent until
    a `final_answer` is returned or max_iters is reached.
    """

    def __init__(self, llm, tools: Dict[str, Callable[..., Any]], max_iters: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_iters = max_iters

    async def run(self, prompt: str, context: Dict[str, Any] = None, event_queue: "asyncio.Queue" = None) -> Dict[str, Any]:
        """Run the ReAct loop. If event_queue is provided, push events as dicts into it for streaming.

        Events pushed:
        - {"type": "thought", "thought": str}
        - {"type": "action", "action": str, "action_input": obj}
        - {"type": "observation", "observation": str}
        - {"type": "final", "final_answer": str}
        """
        context = context or {}
        history = []
        for i in range(self.max_iters):
            # Construct the prompt: include history of observations
            full_prompt = prompt + "\n\nHistory:\n" + "\n".join(history)
            resp = await self.llm.generate(full_prompt)
            text = resp.get("text", "")
            # try to parse JSON, with a simple re-prompt-on-invalid-JSON fallback
            payload = None
            attempts = 0
            while attempts < 2 and payload is None:
                try:
                    payload = json.loads(text)
                except Exception:
                    # re-prompt the model to return valid JSON only
                    attempts += 1
                    warn = (
                        "Your previous reply was not valid JSON. "
                        "Please respond with ONLY valid JSON with keys: thought (string), action (string|null), action_input (object|null), final_answer (string|null)."
                    )
                    resp = await self.llm.generate(full_prompt + "\n\n" + warn)
                    text = resp.get("text", "")
            if payload is None:
                # still invalid — return the raw text as final answer for debugging
                if event_queue is not None:
                    await event_queue.put({"type": "final", "final_answer": text, "iterations": i + 1, "note": "invalid_json"})
                return {"final_answer": text, "iterations": i + 1, "note": "invalid_json"}

            thought = payload.get("thought")
            action = payload.get("action")
            action_input = payload.get("action_input")
            final_answer = payload.get("final_answer")

            # emit thought event
            if event_queue is not None:
                await event_queue.put({"type": "thought", "thought": thought, "iteration": i + 1})

            if final_answer:
                if event_queue is not None:
                    await event_queue.put({"type": "final", "final_answer": final_answer, "iteration": i + 1})
                return {"final_answer": final_answer, "iterations": i + 1}

            if not action:
                # nothing to do
                if event_queue is not None:
                    await event_queue.put({"type": "final", "final_answer": None, "reason": "no action", "iteration": i + 1})
                return {"final_answer": None, "reason": "no action", "iterations": i + 1}

            tool = self.tools.get(action)
            if not tool:
                observation = f"Unknown tool: {action}"
            else:
                # emit action event
                if event_queue is not None:
                    await event_queue.put({"type": "action", "action": action, "action_input": action_input, "iteration": i + 1})
                # Support async tool
                if asyncio.iscoroutinefunction(tool):
                    observation = await tool(action_input or {})
                else:
                    observation = tool(action_input or {})

            # emit observation event
            if event_queue is not None:
                await event_queue.put({"type": "observation", "observation": observation, "iteration": i + 1})

            # Append observation to history for next prompt
            history.append(f"Observation: {observation}")

        if event_queue is not None:
            await event_queue.put({"type": "final", "final_answer": None, "reason": "max_iters_reached", "iterations": self.max_iters})
        return {"final_answer": None, "reason": "max_iters_reached", "iterations": self.max_iters}
