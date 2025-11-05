import asyncio
import json
from src.agent_demo.llm import MockLLM
from src.agent_demo.workflow import WorkflowRunner
from src.agent_demo import tools as tools_mod


def test_hybrid_workflow_runs():
    async def _run():
        with open("examples/hybrid_workflow.json", "r", encoding="utf-8") as f:
            workflow = json.load(f)
        llm = MockLLM()
        tools = {"search": tools_mod.search_tool, "run_tests": tools_mod.run_tests_tool}
        runner = WorkflowRunner(llm, tools=tools)
        result = await runner.run(workflow)
        memory = result.get("memory", {})
        # Basic assertions for demo: we expect the keys present
        assert "summary" in memory
        assert "investigation" in memory
        assert "report" in memory

    asyncio.run(_run())
