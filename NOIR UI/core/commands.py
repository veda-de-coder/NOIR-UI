"""
Command pattern implementation for undo/redo functionality.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Any
from event_bus import EventBus, EventType

@dataclass
class CommandState:
    """Represents the state change for a command."""
    affected_components: Set[str] = field(default_factory=set)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)

class Command(ABC):
    """Abstract base class for all commands with optimized state management."""
    
    def __init__(self):
        self.state = CommandState()
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass
    
    def store_state(self, component_id: str, property_name: str, old_value: Any, new_value: Any):
        """Store state change for efficient undo/redo."""
        self.state.affected_components.add(component_id)
        if component_id not in self.state.old_values:
            self.state.old_values[component_id] = {}
            self.state.new_values[component_id] = {}
        self.state.old_values[component_id][property_name] = old_value
        self.state.new_values[component_id][property_name] = new_value

class CommandHistory:
    """Manages command history for undo/redo operations."""
    
    def __init__(self, event_bus: EventBus):
        self._history: List[Command] = []
        self._current: int = -1
        self._event_bus = event_bus
    
    def execute(self, command: Command) -> None:
        """Execute a new command and add it to history."""
        # Remove all commands after current position
        self._history = self._history[:self._current + 1]
        
        # Execute the command and add to history
        command.execute()
        self._history.append(command)
        self._current += 1
        
        # Notify state change
        self._event_bus.publish_from(EventType.STATE_CHANGED)
    
    def undo(self) -> None:
        """Undo the last command."""
        if self._current >= 0:
            self._history[self._current].undo()
            self._current -= 1
            self._event_bus.publish_from(EventType.UNDO_PERFORMED)
    
    def redo(self) -> None:
        """Redo the last undone command."""
        if self._current + 1 < len(self._history):
            self._current += 1
            self._history[self._current].execute()
            self._event_bus.publish_from(EventType.REDO_PERFORMED)
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self._current >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self._current + 1 < len(self._history)

# Example concrete commands
class CreateComponentCommand(Command):
    """Command for creating a new component."""
    
    def __init__(self, component_registry, component_type: str, properties: dict):
        self.registry = component_registry
        self.component_type = component_type
        self.properties = properties
        self.created_component = None
    
    def execute(self) -> None:
        self.created_component = self.registry.create_component(
            self.component_type,
            self.properties
        )
    
    def undo(self) -> None:
        if self.created_component:
            self.registry.delete_component(self.created_component.id)
            self.created_component = None

class DeleteComponentCommand(Command):
    """Command for deleting a component."""
    
    def __init__(self, component_registry, component_id: str):
        self.registry = component_registry
        self.component_id = component_id
        self.deleted_component = None
    
    def execute(self) -> None:
        self.deleted_component = self.registry.get_component(self.component_id)
        self.registry.delete_component(self.component_id)
    
    def undo(self) -> None:
        if self.deleted_component:
            self.registry.restore_component(self.deleted_component)
