from collections import defaultdict
from typing import Any, Callable, Type

from plain2code_events import BaseEvent


class EventBus:
    def __init__(self):
        self._listeners: defaultdict[Type[BaseEvent], list[Callable[[Any], None]]] = defaultdict(list)
        self._main_thread_callback: Callable[[Callable], None] | None = None
        self._ready_callbacks: list[Callable[[], None]] = []

    def register_main_thread_callback(self, fn: Callable[[Callable], None]):
        """Set the function to call listeners from the main thread (e.g., Textual app.call_from_thread)."""
        self._main_thread_callback = fn

        # Notify anyone waiting for the event bus to be ready
        for callback in self._ready_callbacks:
            callback()
        self._ready_callbacks.clear()

    def on_ready(self, callback: Callable[[], None]):
        """Register a callback to be called when the event bus is ready."""
        if self._main_thread_callback:
            # Already ready, call immediately
            callback()
        else:
            # Not ready yet, queue it
            self._ready_callbacks.append(callback)

    def subscribe(self, event_type: Type[BaseEvent], listener: Callable[[Any], None]):
        """Registers a listener for a specific event type."""
        self._listeners[event_type].append(listener)

    def publish(self, event: BaseEvent):
        """Publishes an event to all registered listeners."""

        def _dispatch():
            for listener in self._listeners[type(event)]:
                listener(event)

        if not self._main_thread_callback:
            raise RuntimeError("No main thread callback set. Call register_main_thread_callback() first.")

        self._main_thread_callback(_dispatch)
