from src.agent_demo.templating import render_template


def test_render_basic_template():
    tpl = "Hello {{ inputs.name }}"
    ctx = {"inputs": {"name": "Alice"}, "memory": {}}
    out = render_template(tpl, ctx)
    assert out.strip() == "Hello Alice"


def test_safe_get_helper():
    tpl = "Investigation: {{ get(memory, 'investigation.react_result.final_answer','no') }}"
    ctx = {"inputs": {}, "memory": {"investigation": {"react_result": {"final_answer": "done"}}}}
    out = render_template(tpl, ctx)
    assert "done" in out
