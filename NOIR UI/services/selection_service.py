"""
Selection management service implementation.
"""
from typing import Set, Optional
from core.event_bus import EventBus, EventType

class SelectionService:
    """Service for managing component selection state."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._selected_components: Set[str] = set()
        self._active_component: Optional[str] = None
    
    def select(self, component_id: str):
        """Select a component."""
        self._selected_components.add(component_id)
        self._active_component = component_id
        self._notify_selection_changed()
    
    def deselect(self, component_id: str):
        """Deselect a component."""
        self._selected_components.discard(component_id)
        if self._active_component == component_id:
            self._active_component = next(iter(self._selected_components)) if self._selected_components else None
        self._notify_selection_changed()
    
    def clear_selection(self):
        """Clear all selections."""
        self._selected_components.clear()
        self._active_component = None
        self._notify_selection_changed()
    
    def is_selected(self, component_id: str) -> bool:
        """Check if a component is selected."""
        return component_id in self._selected_components
    
    def get_selected_components(self) -> Set[str]:
        """Get all selected component IDs."""
        return self._selected_components.copy()
    
    def get_active_component(self) -> Optional[str]:
        """Get the active component ID."""
        return self._active_component
    
    def _notify_selection_changed(self):
        """Notify listeners of selection changes."""
        self.event_bus.publish_from(
            EventType.SELECTION_CHANGED,
            {
                'selected': list(self._selected_components),
                'active': self._active_component
            },
            'selection_service'
        )
