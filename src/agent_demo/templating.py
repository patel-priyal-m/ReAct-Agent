from jinja2 import Environment, StrictUndefined
from typing import Any, Dict

env = Environment(undefined=StrictUndefined)


def _safe_get(obj: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get a nested value from a dict-like object using dot notation.

    Example: _safe_get(memory, 'investigation.react_result.final_answer')
    """
    if obj is None:
        return default
    parts = path.split(".")
    cur = obj
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p, default)
        else:
            # not a dict; can't descend
            return default
        if cur is None:
            return default
    return cur


# expose helper to templates
env.globals["get"] = _safe_get


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """Render a Jinja2 template with the provided context.

    The context can contain nested dictionaries (memory, inputs, etc.).
    Use the `get(obj, 'a.b.c', default)` helper in templates for safe nested access.
    """
    template = env.from_string(template_str)
    return template.render(**context)
