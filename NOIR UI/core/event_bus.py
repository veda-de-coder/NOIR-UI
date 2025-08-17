"""
Event bus implementation for decoupled communication between components.
"""
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from enum import Enum, auto

class EventType(Enum):
    """Enumeration of all possible event types in the application."""
    COMPONENT_CREATED = auto()
    COMPONENT_DELETED = auto()
    SELECTION_CHANGED = auto()
    CANVAS_UPDATED = auto()
    UNDO_PERFORMED = auto()
    REDO_PERFORMED = auto()
    STATE_CHANGED = auto()

@dataclass
class Event:
    """Event data structure."""
    type: EventType
    data: Any = None
    source: str = None

class EventBus:
    """
    Central event bus for application-wide communication.
    Implements the Observer pattern for decoupled component communication.
    """
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to an event type with a callback function."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe a callback from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    def publish(self, event: Event):
        """Publish an event to all subscribers."""
        for callback in self._subscribers.get(event.type, []):
            callback(event)

    def publish_from(self, event_type: EventType, data: Any = None, source: str = None):
        """Convenience method to publish an event with data and source."""
        self.publish(Event(event_type, data, source))
