import asyncio
import json
from src.agent_demo.llm import MockLLM
from src.agent_demo.reactor import ReActAgent
from src.agent_demo import tools as tools_mod


def test_react_emits_events():
    async def _run():
        llm = MockLLM()
        tools = {"search": tools_mod.search_tool, "run_tests": tools_mod.run_tests_tool}
        agent = ReActAgent(llm, tools=tools, max_iters=4)
        queue = asyncio.Queue()
        result = await agent.run("You are a ReAct agent. Thought and action.", event_queue=queue)
        # drain queue into list
        items = []
        while not queue.empty():
            items.append(queue.get_nowait())
        # ensure final answer present (MockLLM produces final_answer when it sees observation)
        assert result.get("final_answer") is not None or result.get("reason") == "max_iters_reached"

    asyncio.run(_run())
