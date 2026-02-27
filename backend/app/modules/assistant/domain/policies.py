from dataclasses import dataclass


@dataclass
class AssistantPolicy:
    history_limit: int
    max_tool_iterations: int
