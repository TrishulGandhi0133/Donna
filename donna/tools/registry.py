"""
donna.tools.registry — Tool registration, discovery, and schema generation.

The ``@tool`` decorator is the core mechanism.  Any Python function
decorated with ``@tool`` is automatically registered and its JSON schema
(for LLM function-calling) is auto-generated from the function's
**type hints** and **docstring**.

Example
-------
::

    @tool(name="read_file", safety="green", description="Read a file from disk.")
    def read_file(path: str) -> str:
        \"\"\"Read and return the contents of ``path``.\"\"\"
        return Path(path).read_text()

At startup Donna imports all modules in ``donna/tools/`` and any skill
scripts in ``data/skills/``; decorated functions are auto-discovered.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, get_type_hints

from donna.models.base import ToolSchema

# ---------------------------------------------------------------------------
# Registry storage
# ---------------------------------------------------------------------------

# Python type → JSON Schema type mapping
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


@dataclass
class ToolEntry:
    """A registered tool with its metadata.

    Attributes
    ----------
    name : str
        The name the LLM uses to call this tool.
    func : Callable
        The actual Python function to execute.
    description : str
        Human-readable description (shown to the model).
    safety : str
        ``"green"`` (auto-execute) or ``"red"`` (requires confirmation).
    schema : ToolSchema
        The JSON Schema sent to the model for function-calling.
    """

    name: str
    func: Callable[..., Any]
    description: str
    safety: str  # "green" | "red"
    schema: ToolSchema = field(default_factory=lambda: ToolSchema(name="", description=""))


# The global registry — maps tool name → ToolEntry
_TOOL_REGISTRY: dict[str, ToolEntry] = {}


# ---------------------------------------------------------------------------
# Schema generation
# ---------------------------------------------------------------------------


def _build_parameters_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """Inspect a function's type hints and build a JSON Schema ``parameters`` object.

    Parameters whose names start with ``_`` are skipped (private).
    """
    hints = get_type_hints(func)
    sig = inspect.signature(func)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name.startswith("_"):
            continue

        # Determine JSON type
        py_type = hints.get(param_name, str)
        json_type = _TYPE_MAP.get(py_type, "string")

        prop: dict[str, Any] = {"type": json_type}

        # If the param has a default, it's optional; otherwise required
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            prop["default"] = param.default

        properties[param_name] = prop

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema


# ---------------------------------------------------------------------------
# @tool decorator
# ---------------------------------------------------------------------------


def tool(
    *,
    name: str,
    safety: str = "green",
    description: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that registers a function as a Donna tool.

    Parameters
    ----------
    name : str
        The tool name the LLM will use in ``tool_call.name``.
    safety : str
        ``"green"`` for auto-execute, ``"red"`` for human confirmation.
    description : str
        What the tool does (shown to the LLM).

    Returns
    -------
    The original function, unmodified.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        desc = description or (func.__doc__ or "").strip().split("\n")[0]
        params_schema = _build_parameters_schema(func)

        schema = ToolSchema(
            name=name,
            description=desc,
            parameters=params_schema,
        )

        entry = ToolEntry(
            name=name,
            func=func,
            description=desc,
            safety=safety,
            schema=schema,
        )

        _TOOL_REGISTRY[name] = entry
        return func

    return decorator


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_tool(name: str) -> ToolEntry | None:
    """Look up a tool by name.  Returns ``None`` if not found."""
    return _TOOL_REGISTRY.get(name)


def get_all_tools() -> dict[str, ToolEntry]:
    """Return a copy of the full registry."""
    return dict(_TOOL_REGISTRY)


def get_tool_schemas(names: list[str] | None = None) -> list[ToolSchema]:
    """Return ``ToolSchema`` objects for the given tool names.

    If *names* is ``None``, return schemas for **all** registered tools.
    """
    if names is None:
        return [e.schema for e in _TOOL_REGISTRY.values()]
    return [
        _TOOL_REGISTRY[n].schema
        for n in names
        if n in _TOOL_REGISTRY
    ]


def register_function(
    func: Callable[..., Any],
    *,
    name: str,
    safety: str = "green",
    description: str = "",
) -> None:
    """Programmatically register a function as a tool (used for skills hot-loading)."""
    tool(name=name, safety=safety, description=description)(func)
