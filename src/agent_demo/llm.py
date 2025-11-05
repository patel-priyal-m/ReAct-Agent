import os
import json
import asyncio
from typing import Dict, Any

try:
    import openai
except Exception:
    openai = None


class LLMAdapter:
    async def generate(self, prompt: str, **opts) -> Dict[str, Any]:
        raise NotImplementedError()


class MockLLM(LLMAdapter):
    """A deterministic mock LLM for offline demos. It inspects the prompt and returns predictable JSON/text.
    """

    async def generate(self, prompt: str, **opts) -> Dict[str, Any]:
        # Very small heuristic-based mock responses for demo purposes
        lower = prompt.lower()
        if "summarize" in lower or "summarise" in lower:
            return {"text": "{\"summary\": \"This function computes the factorial of a number recursively.\"}"}
        if "generate tests" in lower or "test cases" in lower:
            return {"text": "{\"tests\": [\"test_factorial_positive\", \"test_factorial_zero\"]}"}

        # ReAct behavior: when called initially, suggest an action (e.g., search).
        # After the controller appends an Observation to the prompt, the mock will return a final_answer.
        if "observation:" in lower:
            # We have at least one observation from a tool; return a final answer.
            return {
                "text": json.dumps({
                    "thought": "I have enough information from the observation.",
                    "action": None,
                    "action_input": None,
                    "final_answer": "Investigation result: The recursive factorial lacks a guard for negative inputs and may hit recursion limits for large n. Recommend adding input validation and an iterative implementation for large values.",
                })
            }

        if "react" in lower or "thought" in lower:
            # Initial ReAct reply: request a search action
            return {
                "text": json.dumps({
                    "thought": "I should search for known pitfalls of recursive factorial implementations.",
                    "action": "search",
                    "action_input": {"query": "recursive factorial common bugs"},
                    "final_answer": None,
                })
            }
        # If asked to produce a short markdown report, try to synthesize one using any summary/investigation
        if "produce a short markdown report" in lower or "short markdown report" in lower:
            # Try to heuristically extract the summary and investigation values from common phrasing
            def _extract_between(text: str, start_marker: str, end_marker: str) -> str:
                try:
                    s = text.index(start_marker) + len(start_marker)
                    e = text.index(end_marker, s)
                    return text[s:e].strip()
                except Exception:
                    return ""

            summary = _extract_between(prompt, "Using the summary (", ")")
            investigation = _extract_between(prompt, "investigation (", ")")
            md = "# Report\n\n"
            if summary:
                md += "## Summary\n" + summary + "\n\n"
            if investigation:
                md += "## Investigation\n" + investigation + "\n\n"
            if not summary and not investigation:
                md += "No sufficient information available to produce a report."

            return {"text": md}
        # default fallback
        return {"text": "I don't know exactly; please provide more details."}


class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str = None):
        if openai is None:
            raise RuntimeError("openai package not installed. Install it or use MockLLM")
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        openai.api_key = self.key

    async def generate(self, prompt: str, **opts) -> Dict[str, Any]:
        # Use chat completions if available; this is a minimal wrapper
        model = opts.get("model", "gpt-3.5-turbo")
        max_tokens = opts.get("max_tokens", 512)
        temperature = opts.get("temperature", 0.2)
        mode = opts.get("mode")

        # openai Python client is sync; run in thread
        loop = asyncio.get_event_loop()

        def _call():
            # If caller requests ReAct mode, provide a few-shot prompt + system instruction to encourage strict JSON
            if mode == "react":
                system_msg = (
                    "You are an assistant that follows the ReAct protocol. "
                    "All replies MUST be valid JSON and use only the following keys: \n"
                    "- thought (string)\n- action (string or null)\n- action_input (object or null)\n- final_answer (string or null)\n"
                )
                # small few-shot example
                example_user = (
                    "Question: Is 2+2 equal to 4?\nRespond with a short chain-of-thought as 'thought', then 'action': null and 'final_answer'."
                )
                example_assistant = json.dumps({
                    "thought": "This is basic arithmetic.",
                    "action": None,
                    "action_input": None,
                    "final_answer": "Yes, 2+2 equals 4."
                })

                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": example_user},
                    {"role": "assistant", "content": example_assistant},
                    {"role": "user", "content": prompt},
                ]
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            return resp

        resp = await loop.run_in_executor(None, _call)
        text = resp.choices[0].message.content
        return {"text": text}
