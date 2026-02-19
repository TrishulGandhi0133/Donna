"""
donna.tools — Tool registry and built-in tools.

Importing this package **auto-registers** all built-in tools by
importing the tool modules.  After import, use ``registry.get_all_tools()``
or ``registry.get_tool_schemas()`` to access them.
"""

# Import tool modules so their @tool decorators execute and register
from donna.tools import filesystem  # noqa: F401
from donna.tools import shell_exec  # noqa: F401
from donna.tools import clipboard   # noqa: F401
from donna.tools import process     # noqa: F401

from donna.tools.registry import (
    get_all_tools,
    get_tool,
    get_tool_schemas,
    register_function,
)

__all__ = [
    "get_all_tools",
    "get_tool",
    "get_tool_schemas",
    "register_function",
]
