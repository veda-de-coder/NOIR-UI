"""
Status bar implementation.
"""
import tkinter as tk
from tkinter import ttk
from core.event_bus import EventBus, EventType
from core.config import Config

class StatusBar:
    """Status bar implementation for displaying application status."""
    
    def __init__(self, parent: tk.Widget, event_bus: EventBus, config: Config):
        self.parent = parent
        self.event_bus = event_bus
        self.config = config
        
        self._create_widgets()
        self._setup_event_handlers()
    
    def _create_widgets(self):
        """Create status bar widgets."""
        self.frame = ttk.Frame(self.parent)
        
        # Status message
        self.status_label = ttk.Label(
            self.frame,
            text="Ready"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Zoom level
        self.zoom_label = ttk.Label(
            self.frame,
            text="Zoom: 100%"
        )
        self.zoom_label.pack(side=tk.RIGHT, padx=5)
        
        # Coordinates
        self.coords_label = ttk.Label(
            self.frame,
            text="X: 0, Y: 0"
        )
        self.coords_label.pack(side=tk.RIGHT, padx=5)
        
        # Selection count
        self.selection_label = ttk.Label(
            self.frame,
            text="Selected: 0"
        )
        self.selection_label.pack(side=tk.RIGHT, padx=5)
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        self.event_bus.subscribe(
            EventType.STATE_CHANGED,
            self._handle_state_changed
        )
        self.event_bus.subscribe(
            EventType.SELECTION_CHANGED,
            self._handle_selection_changed
        )
        self.event_bus.subscribe(
            EventType.CANVAS_UPDATED,
            self._handle_canvas_updated
        )
    
    def get_widget(self) -> ttk.Frame:
        """Get the status bar widget."""
        return self.frame
    
    def set_status(self, message: str):
        """Set the status message."""
        self.status_label.config(text=message)
    
    def _handle_state_changed(self, event):
        """Handle state change events."""
        if 'message' in event.data:
            self.set_status(event.data['message'])
    
    def _handle_selection_changed(self, event):
        """Handle selection change events."""
        selected_count = len(event.data['selected'])
        self.selection_label.config(
            text=f"Selected: {selected_count}"
        )
    
    def _handle_canvas_updated(self, event):
        """Handle canvas update events."""
        # Update zoom level
        zoom_percent = int(event.data['zoom_level'] * 100)
        self.zoom_label.config(
            text=f"Zoom: {zoom_percent}%"
        )
        
        # Update coordinates if available
        if 'cursor' in event.data:
            x, y = event.data['cursor']
            self.coords_label.config(
                text=f"X: {int(x)}, Y: {int(y)}"
            )
