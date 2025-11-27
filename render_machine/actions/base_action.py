from abc import abstractmethod
from typing import Any

from render_machine.render_context import RenderContext


class BaseAction:
    def __init__(self):
        pass

    @abstractmethod
    def execute(self, _render_context: RenderContext, _previous_action_payload: Any | None):
        """
        Execute the action with the given render context and optional previous action payload.

        Returns:
            tuple: (outcome, payload) where outcome is a string and payload can be any object or None
        """
        pass
