import logging
from typing import List, Tuple

from app.models.tool_models import ToolDefinition
from app.repositories.database_repository import DatabaseRepository
from .base import BaseTool

logger = logging.getLogger(__name__)


class BrowsingStatsTool(BaseTool):
    """Provide aggregate browsing statistics for a user."""

    _DEFINITION = ToolDefinition(
        name="get_browsing_stats",
        description=(
            "Get overall browsing statistics: total sessions, total pages visited, "
            "total themes/clusters, top visited domains, and date range of activity. "
            "Use when the user asks 'how much do I browse', 'what are my most visited "
            "sites', or any general statistics about their browsing."
        ),
        parameters={
            "type": "object",
            "properties": {
                "top_domains_limit": {
                    "type": "integer",
                    "description": "Number of top domains to return (default 10)",
                },
            },
            "required": [],
        },
    )

    def __init__(self, db_repository: DatabaseRepository):
        self.db_repository = db_repository

    @property
    def definition(self) -> ToolDefinition:
        return self._DEFINITION

    async def execute(self, user_id: int, arguments: dict) -> Tuple[str, List[dict]]:
        top_domains_limit = arguments.get("top_domains_limit", 10)

        stats = self.db_repository.get_user_browsing_stats(user_id)
        top_domains = self.db_repository.get_top_domains(user_id, limit=top_domains_limit)

        if not stats:
            return "Could not retrieve browsing statistics.", []

        lines = [
            "Browsing statistics:",
            f"• Total sessions: {stats['session_count']}",
            f"• Total themes/clusters: {stats['cluster_count']}",
            f"• Total pages visited: {stats['item_count']}",
            f"• Activity range: {stats.get('earliest_session', '?')} → {stats.get('latest_session', '?')}",
        ]

        if top_domains:
            lines.append("\nTop visited domains:")
            for d in top_domains:
                lines.append(f"• {d['domain']} ({d['count']} pages)")

        return "\n".join(lines), []
