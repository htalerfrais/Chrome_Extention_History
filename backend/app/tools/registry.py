import logging
from typing import List, Optional, Tuple

from app.models.tool_models import ToolDefinition, ToolCall, ToolResult
from .base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry that maps tool names to BaseTool instances.

    Consumers (ChatService, future QuizService, etc.) receive a ToolRegistry
    and can query available definitions or execute tool calls without knowing
    about individual tool implementations.
    """

    def __init__(self, tools: List[BaseTool]):
        self._tools = {t.definition.name: t for t in tools}
        logger.info(f"ToolRegistry initialised with {len(self._tools)} tool(s): {list(self._tools.keys())}")

    def get_definitions(self, names: Optional[List[str]] = None) -> List[ToolDefinition]:
        """Return tool definitions, optionally filtered by name.

        Args:
            names: If provided, only return definitions for these tool names.
                   If None, return all registered definitions.
        """
        if names is None:
            return [t.definition for t in self._tools.values()]
        return [self._tools[n].definition for n in names if n in self._tools]

    async def execute(
        self, tool_call: ToolCall, user_id: int
    ) -> Tuple[ToolResult, List[dict]]:
        """Execute a tool call and return (ToolResult, source_dicts).

        Wraps the underlying BaseTool.execute() output into a ToolResult
        so consumers don't need to build it themselves.
        """
        tool = self._tools.get(tool_call.name)
        if not tool:
            logger.warning(f"Unknown tool call: {tool_call.name}")
            return (
                ToolResult(call_id=tool_call.id, content=f"Unknown tool: {tool_call.name}"),
                [],
            )

        try:
            content, sources = await tool.execute(user_id, tool_call.arguments)
            return ToolResult(call_id=tool_call.id, content=content), sources
        except Exception as e:
            logger.error(f"Tool '{tool_call.name}' execution failed: {e}")
            return (
                ToolResult(call_id=tool_call.id, content=f"Tool execution error: {e}"),
                [],
            )
