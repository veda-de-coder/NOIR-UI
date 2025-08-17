"""
Toolbar management implementation.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable
from core.event_bus import EventBus, EventType
from core.config import Config


class ToolbarManager:
    """Manages the application toolbar and its actions."""
    
    def __init__(self, parent: tk.Widget, event_bus: EventBus, config: Config):
        self.parent = parent
        self.event_bus = event_bus
        self.config = config
        
        self._create_toolbar()
        self._setup_event_handlers()
    
    def _create_toolbar(self):
        """Create the toolbar and its buttons."""
        self.frame = ttk.Frame(self.parent)
        
        # File operations
        self._add_button("New", self._on_new)
        self._add_button("Open", self._on_open)
        self._add_button("Save", self._on_save)
        self._add_separator()
        
        # Edit operations
        self._add_button("Undo", self._on_undo)
        self._add_button("Redo", self._on_redo)
        self._add_separator()
        
        # View operations
        self._add_button("Zoom In", self._on_zoom_in)
        self._add_button("Zoom Out", self._on_zoom_out)
        self._add_button("Reset View", self._on_reset_view)
        self._add_separator()
        
        # Component operations
        self._add_button("Add Component", self._on_add_component)
        self._add_button("Delete", self._on_delete)
        self._add_button("Duplicate", self._on_duplicate)
    
    def _add_button(self, text: str, command: Callable):
        """Add a button to the toolbar."""
        button = ttk.Button(
            self.frame,
            text=text,
            command=command
        )
        button.pack(side=tk.LEFT, padx=2)
    
    def _add_separator(self):
        """Add a separator to the toolbar."""
        separator = ttk.Separator(
            self.frame,
            orient=tk.VERTICAL
        )
        separator.pack(side=tk.LEFT, padx=5, fill=tk.Y)
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        self.event_bus.subscribe(
            EventType.STATE_CHANGED,
            self._handle_state_changed
        )
    
    def get_widget(self) -> ttk.Frame:
        """Get the toolbar widget."""
        return self.frame
    
    def _on_new(self):
        """Handle New button click."""
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'action': 'new_project'},
            'toolbar'
        )
    
    def _on_open(self):
        """Handle Open button click."""
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'action': 'open_project'},
            'toolbar'
        )
    
    def _on_save(self):
        """Handle Save button click."""
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'action': 'save_project'},
            'toolbar'
        )
    
    def _on_undo(self):
        """Handle Undo button click."""
        self.event_bus.publish_from(
            EventType.UNDO_PERFORMED,
            None,
            'toolbar'
        )
    
    def _on_redo(self):
        """Handle Redo button click."""
        self.event_bus.publish_from(
            EventType.REDO_PERFORMED,
            None,
            'toolbar'
        )
    
    def _on_zoom_in(self):
        """Handle Zoom In button click."""
        self.event_bus.publish_from(
            EventType.CANVAS_UPDATED,
            {'action': 'zoom_in'},
            'toolbar'
        )
    
    def _on_zoom_out(self):
        """Handle Zoom Out button click."""
        self.event_bus.publish_from(
            EventType.CANVAS_UPDATED,
            {'action': 'zoom_out'},
            'toolbar'
        )
    
    def _on_reset_view(self):
        """Handle Reset View button click."""
        self.event_bus.publish_from(
            EventType.CANVAS_UPDATED,
            {'action': 'reset_view'},
            'toolbar'
        )
    
    def _on_add_component(self):
        """Handle Add Component button click."""
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'action': 'add_component'},
            'toolbar'
        )
    
    def _on_delete(self):
        """Handle Delete button click."""
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'action': 'delete_component'},
            'toolbar'
        )
    
    def _on_duplicate(self):
        """Handle Duplicate button click."""
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'action': 'duplicate_component'},
            'toolbar'
        )
        
    def _handle_state_changed(self, event):
        """Handle application state changes to update toolbar button states."""
        if not hasattr(self, 'frame'):  # Toolbar not initialized yet
            return

        # Get all button widgets from the toolbar frame
        buttons = [child for child in self.frame.winfo_children() 
                if isinstance(child, ttk.Button)]
        
        # Create a mapping of button texts to their commands
        button_actions = {
            "New": self._on_new,
            "Open": self._on_open,
            "Save": self._on_save,
            "Undo": self._on_undo,
            "Redo": self._on_redo,
            "Zoom In": self._on_zoom_in,
            "Zoom Out": self._on_zoom_out,
            "Reset View": self._on_reset_view,
            "Add Component": self._on_add_component,
            "Delete": self._on_delete,
            "Duplicate": self._on_duplicate
        }

        # Default all buttons to normal state
        for button in buttons:
            button.state(['!disabled'])

        # Disable buttons based on application state
        if 'project_loaded' not in event.data or not event.data['project_loaded']:
            # No project loaded - disable project-dependent buttons
            for action in ["Save", "Add Component", "Delete", "Duplicate"]:
                self._disable_button(buttons, action)
        
        if 'has_unsaved_changes' in event.data and not event.data['has_unsaved_changes']:
            # No unsaved changes - disable Save button
            self._disable_button(buttons, "Save")
        
        if 'can_undo' in event.data and not event.data['can_undo']:
            self._disable_button(buttons, "Undo")
        
        if 'can_redo' in event.data and not event.data['can_redo']:
            self._disable_button(buttons, "Redo")
        
        if 'selection_empty' in event.data and event.data['selection_empty']:
            # Nothing selected - disable selection-dependent buttons
            for action in ["Delete", "Duplicate"]:
                self._disable_button(buttons, action)

        # Special case for zoom buttons
        if 'zoom_level' in event.data:
            max_zoom = self.config.ui.get('max_zoom', 5.0)
            min_zoom = self.config.ui.get('min_zoom', 0.1)
            
            if event.data['zoom_level'] >= max_zoom:
                self._disable_button(buttons, "Zoom In")
            
            if event.data['zoom_level'] <= min_zoom:
                self._disable_button(buttons, "Zoom Out")

    def _disable_button(self, buttons, action_text):
        """Helper method to disable a specific button."""
        for button in buttons:
            if button['text'] == action_text:
                button.state(['disabled'])
                break