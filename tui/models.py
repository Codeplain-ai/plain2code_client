"""Data models for Plain2Code TUI components."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Substate:
    """Represents a substate item that can be nested.

    Attributes:
        text: The display text for this substate
        children: Optional list of child substates for nested hierarchies

    Example:
        # Simple flat substate
        Substate("Running unit tests")

        # Nested substates
        Substate("Running unit tests", children=[
            Substate("Refactoring code")
        ])

        # Deep nesting (up to 4 levels)
        Substate("Fixing unit tests", children=[
            Substate("Attempt 1/3", children=[
                Substate("Analyzing error", children=[
                    Substate("Applying patch")
                ])
            ])
        ])
    """

    text: str
    children: Optional[list["Substate"]] = None

    def add_child(self, child: "Substate") -> "Substate":
        """Add a child substate.

        This method supports fluent API for building nested structures.

        Args:
            child: The Substate object to add as a child

        Returns:
            Self for method chaining

        Example:
            substate = Substate("Parent")
            substate.add_child(Substate("Child 1"))
            substate.add_child(Substate("Child 2"))
        """
        if self.children is None:
            self.children = []
        self.children.append(child)
        return self
