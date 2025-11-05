import asyncio
import json
import argparse
from src.agent_demo.llm import MockLLM, OpenAIAdapter
from src.agent_demo.workflow import WorkflowRunner
from src.agent_demo import tools as tools_mod


async def main(use_openai: bool = False, code: str | None = None):
    # load workflow
    with open("examples/hybrid_workflow.json", "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # If code provided, inject into entry_inputs.function_code
    if code:
        workflow.setdefault("entry_inputs", {})["function_code"] = code

    if use_openai:
        adapter = OpenAIAdapter()
    else:
        adapter = MockLLM()

    tools = {
        "search": tools_mod.search_tool,
        "run_tests": tools_mod.run_tests_tool,
    }

    runner = WorkflowRunner(adapter, tools=tools)
    result = await runner.run(workflow)
    print("--- RUN RESULT ---")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-openai", action="store_true", help="Use OpenAI adapter instead of mock")
    parser.add_argument("--code", type=str, help="Provide code as a string to override entry input function_code")
    parser.add_argument("--code-file", type=str, help="Path to a file containing code to run through the workflow")
    args = parser.parse_args()
    code = None
    if args.code_file:
        with open(args.code_file, "r", encoding="utf-8") as cf:
            code = cf.read()
    elif args.code:
        code = args.code

    asyncio.run(main(use_openai=args.use_openai, code=code))
