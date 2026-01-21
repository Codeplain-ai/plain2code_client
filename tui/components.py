from enum import Enum

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Static

from spinner import Spinner

from .models import Substate


class ScriptOutputType(str, Enum):
    UNIT_TEST_OUTPUT_TEXT = "Latest unit test script execution output: "
    CONFORMANCE_TEST_OUTPUT_TEXT = "Latest conformance tests script execution output: "
    TESTING_ENVIRONMENT_OUTPUT_TEXT = "Latest testing environment preparation script execution output: "

    @staticmethod
    def get_max_label_width(active_types: list["ScriptOutputType"]) -> int:
        """Get the maximum width of the active script output labels.

        Args:
            active_types: List of ScriptOutputType enum members that are currently active

        Returns:
            Maximum width among the active label types
        """
        if not active_types:
            return 0
        return max(len(script_type.value) for script_type in active_types)

    def get_padded_label(self, active_types: list["ScriptOutputType"]) -> str:
        """Get the label right-padded to align with other active labels.

        Args:
            active_types: List of ScriptOutputType enum members that are currently active

        Returns:
            Right-aligned label padded to match the longest active label
        """
        max_width = ScriptOutputType.get_max_label_width(active_types)
        return self.value.rjust(max_width)


class TUIComponents(str, Enum):
    RENDER_MODULE_NAME_WIDGET = "render-module-name-widget"
    RENDER_ID_WIDGET = "render-id-widget"
    RENDER_STATUS_WIDGET = "render-status-widget"
    UNIT_TEST_SCRIPT_OUTPUT_WIDGET = "unit-test-script-output-widget"
    CONFORMANCE_TESTS_SCRIPT_OUTPUT_WIDGET = "conformance-tests-script-output-widget"
    TESTING_ENVIRONMENT_SCRIPT_OUTPUT_WIDGET = "testing-environment-script-output-widget"

    # FRID Progress widgets
    FRID_PROGRESS = "frid-progress"
    FRID_PROGRESS_HEADER = "frid-progress-header"
    FRID_PROGRESS_RENDER_FR = "frid-progress-render-fr"
    FRID_PROGRESS_UNIT_TEST = "frid-progress-unit-test"
    FRID_PROGRESS_REFACTORING = "frid-progress-refactoring"
    FRID_PROGRESS_CONFORMANCE_TEST = "frid-progress-conformance-test"

    CONTENT_SWITCHER = "content-switcher"
    DASHBOARD_VIEW = "dashboard-view"
    LOG_VIEW = "log-view"
    LOG_WIDGET = "log-widget"
    LOG_FILTER = "log-filter"


class ProgressItem(Vertical):
    """A vertical container for a status, description, and substates."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"

    def __init__(self, initial_text: str, **kwargs):
        super().__init__(**kwargs)
        self.initial_text = initial_text

    def compose(self):
        # Main row with status and description
        with Horizontal(id=f"{self.id}-main-row", classes="progress-main-row"):
            yield Static(self._get_status_text(self.PENDING), classes=f"status {self.PENDING}")
            yield Static(self.initial_text, classes="description")
        # Substates container (full width, aligned to left)
        yield Vertical(id=f"{self.id}-substates", classes="substates-container")

    def _get_status_text(self, status: str) -> str:
        """Get the display text for a given status."""
        if status == self.COMPLETED:
            return "✓ completed"
        elif status == self.PROCESSING:
            return "◉ processing"
        elif status == self.STOPPED:
            return "◼ stopped"
        else:
            return "○ pending"

    async def update_status(self, status: str):
        # TODO: Move to plain2code_tui.py
        try:
            # Get the main row container
            main_row = self.query_one(f"#{self.id}-main-row", Horizontal)

            # Remove existing status widget
            try:
                old_status = main_row.query_one(".status")
                await old_status.remove()
            except Exception:
                pass

            # Add appropriate widget based on status
            if status == self.PROCESSING:
                # Use spinner for processing state
                spinner = Spinner(text="processing", classes=f"status {status}")
                await main_row.mount(spinner, before=0)
            else:
                # Use static text for pending/completed
                status_widget = Static(self._get_status_text(status), classes=f"status {status}")
                await main_row.mount(status_widget, before=0)

        except Exception:
            pass

    def update_text(self, text: str):
        try:
            self.query_one(".description", Static).update(text)
        except Exception:
            pass

    async def set_substates(self, substates: list[Substate]):
        """Set multiple substates to display as a nested checklist.

        Args:
            substates: List of Substate objects to display (supports nesting up to 4 levels)
        """
        try:
            substates_container = self.query_one(f"#{self.id}-substates", Vertical)
            # Clear existing substates
            await substates_container.remove_children()

            # Render substates recursively
            await self._render_substates_recursive(substates_container, substates, depth=0)

            # Add a newline after all substates for visual separation
            if substates:  # Only add newline if there are substates
                newline_widget = Static("", classes="substate-separator")
                await substates_container.mount(newline_widget)
        except Exception:
            pass

    async def _render_substates_recursive(self, container: Vertical, substates: list[Substate], depth: int):
        """Recursively render substates with proper indentation.

        Args:
            container: The container to mount substates into
            substates: List of Substate objects to render
            depth: Current nesting depth (0-based, max 3 for 4 total levels)
        """
        indent = "    " * depth  # 4 spaces per level

        for substate in substates:
            # Render the current substate
            substate_widget = Static(f"{indent}  └ {substate.text}", classes="substate")
            await container.mount(substate_widget)

            # Recursively render children if they exist
            if substate.children:
                await self._render_substates_recursive(container, substate.children, depth + 1)

    async def clear_substates(self):
        """Clear all substates."""
        try:
            substates_container = self.query_one(f"#{self.id}-substates", Vertical)
            await substates_container.remove_children()
        except Exception:
            pass


class FRIDProgress(Vertical):
    """A widget to display the status of subcomponent tasks."""

    # Display text for progress items (UI-specific)
    IMPLEMENTING_FUNCTIONALITY_TEXT = "Implementing the functionality"
    UNIT_TEST_VALIDATION_TEXT = "Unit tests"
    REFACTORING_TEXT = "Refactoring"
    CONFORMANCE_TEST_VALIDATION_TEXT = "Conformance tests"

    RENDERING_MODULE_TEXT = "Rendering module: "
    RENDERING_FUNCTIONALITY_TEXT = "Rendering functionality:"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_fr_text(self, text: str) -> None:
        try:
            widget = self.query_one(f"#{TUIComponents.FRID_PROGRESS_HEADER.value}", Static)
            widget.update(text)
        except Exception:
            pass

    def update_fr_status(self, status: str) -> None:
        try:
            widget = self.query_one(f"#{TUIComponents.FRID_PROGRESS_RENDER_FR.value}", ProgressItem)
            self.call_later(widget.update_status, status)
        except Exception:
            pass

    def on_mount(self) -> None:
        self.border_title = "FRID Progress"

    def compose(self):
        yield Static(self.RENDERING_MODULE_TEXT, id=TUIComponents.RENDER_MODULE_NAME_WIDGET.value)
        yield Static(self.RENDERING_FUNCTIONALITY_TEXT, id=TUIComponents.FRID_PROGRESS_HEADER.value)
        yield ProgressItem(
            self.IMPLEMENTING_FUNCTIONALITY_TEXT,
            id=TUIComponents.FRID_PROGRESS_RENDER_FR.value,
        )
        yield ProgressItem(
            self.UNIT_TEST_VALIDATION_TEXT,
            id=TUIComponents.FRID_PROGRESS_UNIT_TEST.value,
        )
        yield ProgressItem(
            self.REFACTORING_TEXT,
            id=TUIComponents.FRID_PROGRESS_REFACTORING.value,
        )
        yield ProgressItem(
            self.CONFORMANCE_TEST_VALIDATION_TEXT,
            id=TUIComponents.FRID_PROGRESS_CONFORMANCE_TEST.value,
        )


class ClickableArrow(Static):
    """A clickable arrow widget for expanding/collapsing logs."""

    def __init__(self, is_expanded: bool = False, **kwargs):
        arrow = "▼" if is_expanded else "▶"
        super().__init__(arrow, **kwargs)
        self.classes = "log-arrow"

    def on_click(self, event):
        """Notify parent to toggle expansion."""
        # Bubble up to parent CollapsibleLogEntry
        event.stop()
        parent = self.parent
        if isinstance(parent, CollapsibleLogEntry):
            parent.toggle_expansion()


class CollapsibleLogEntry(Horizontal):
    """A single collapsible log entry that can be clicked to expand/collapse."""

    def __init__(self, logger_name: str, level: str, message: str, timestamp: str = "", **kwargs):
        super().__init__(**kwargs)
        self.logger_name = logger_name
        self.level = level
        self.message = message
        self.timestamp = timestamp
        self.is_expanded = False
        self.classes = f"log-entry log-{level.lower()}"

    def compose(self):
        # Start with collapsed view - arrow and full message text side by side
        yield ClickableArrow(id="arrow")
        yield Static(self.message, classes="log-summary")

    def toggle_expansion(self):
        """Toggle the expansion state of this log entry."""
        self.is_expanded = not self.is_expanded
        self.call_later(self.refresh_display)

    async def refresh_display(self):
        """Update the display based on expanded state."""
        # Remove all children
        await self.remove_children()

        if self.is_expanded:
            # Expanded view: shows arrow, full message, and structured metadata
            await self.mount(ClickableArrow(is_expanded=True))
            expanded_text = f"{self.message}\n"
            expanded_text += f"   Level: {self.level}\n"
            expanded_text += f"   Location: {self.logger_name}\n"
            expanded_text += f"   Time: {self.timestamp}"
            await self.mount(Static(expanded_text, classes="log-expanded"))
        else:
            # Collapsed view: shows arrow and full message only
            await self.mount(ClickableArrow(is_expanded=False))
            await self.mount(Static(self.message, classes="log-summary"))


class StructuredLogView(VerticalScroll):
    """A scrollable container for collapsible log entries."""

    # Log level hierarchy (lower number = lower priority)
    LOG_LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_level = "DEBUG"  # Show all by default

    def _should_show_log(self, level: str) -> bool:
        """Check if log should be shown based on minimum level."""
        log_priority = self.LOG_LEVELS.get(level, 0)
        min_priority = self.LOG_LEVELS.get(self.min_level, 0)
        return log_priority >= min_priority

    async def add_log(self, logger_name: str, level: str, message: str, timestamp: str = ""):
        """Add a new log entry."""
        entry = CollapsibleLogEntry(logger_name, level, message, timestamp)

        # Only show if level is >= minimum level
        if not self._should_show_log(level):
            entry.display = False

        await self.mount(entry)
        # Auto-scroll to bottom to show latest logs
        self.scroll_end(animate=False)

    def filter_logs(self, min_level: str):
        """Show/hide logs based on minimum level."""
        self.min_level = min_level

        # Update visibility of all existing log entries
        for entry in self.query(CollapsibleLogEntry):
            entry.display = self._should_show_log(entry.level)


class LogFilterChanged(Message):
    """Message sent when log filter changes."""

    def __init__(self, min_level: str):
        super().__init__()
        self.min_level = min_level


class LogLevelFilter(Horizontal):
    """Filter logs by minimum level with buttons."""

    LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_level = "DEBUG"

    def compose(self):
        yield Static("Level: ", classes="filter-label")
        for level in self.LEVELS:
            variant = "primary" if level == self.current_level else "default"
            yield Button(level, id=f"filter-{level.lower()}", variant=variant, classes="filter-button")  # type: ignore[arg-type]

    def on_button_pressed(self, event):
        """Handle level button press."""
        # Extract level from button ID
        button_id = event.button.id
        if button_id and button_id.startswith("filter-"):
            level = button_id.replace("filter-", "").upper()
            self.current_level = level

            # Update button variants
            for btn in self.query(Button):
                if btn.id == f"filter-{level.lower()}":
                    btn.variant = "primary"
                else:
                    btn.variant = "default"

            # Notify parent to refresh log visibility
            self.post_message(LogFilterChanged(level))
