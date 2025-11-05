from typing import Dict, Any


async def search_tool(input: Dict[str, Any]) -> str:
    query = input.get("query", "")
    # Mock search results for demo
    if "recursive factorial" in query.lower() or "factorial" in query.lower():
        return "Search results: recursive factorial may hit recursion limits and needs guard for negative inputs."
    return "Search results: no relevant results found."


async def run_tests_tool(input: Dict[str, Any]) -> str:
    # Very naive simulator: if code contains 'factorial' and not 'if n < 0' then fail
    code = input.get("code", "")
    if "factorial" in code and "if n < 0" not in code:
        return "Tests failed: no negative input guard; stack depth may be exceeded for large inputs."
    return "Tests passed: all checks OK."
