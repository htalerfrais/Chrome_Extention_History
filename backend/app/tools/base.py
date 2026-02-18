from abc import ABC, abstractmethod
from typing import List, Tuple

from app.models.tool_models import ToolDefinition


class BaseTool(ABC):
    """Abstract base class for all LLM-callable tools.

    Each tool provides:
      - A provider-agnostic ToolDefinition (name, description, JSON Schema params)
      - An async execute method returning (text_content, source_dicts)
    """

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the provider-agnostic tool definition."""
        ...

    @abstractmethod
    async def execute(self, user_id: int, arguments: dict) -> Tuple[str, List[dict]]:
        """Execute the tool and return results.

        Args:
            user_id: Authenticated user id.
            arguments: Parsed arguments from the LLM tool call.

        Returns:
            Tuple of (text_content, source_dicts).
            - text_content: formatted string fed back to the LLM.
            - source_dicts: list of {url, title, visit_time, url_hostname}
              for browsing items used as sources. Empty list when the tool
              does not produce browsing-item sources.
        """
        ...
