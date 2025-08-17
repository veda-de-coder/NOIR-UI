"""
Main window implementation.
"""
import tkinter as tk
from typing import Optional
from core.event_bus import EventBus, EventType
from core.config import Config
from core.service_container import ServiceContainer
from ui.canvas_manager import CanvasManager
from ui.panel_manager import PanelManager
from ui.status_bar import StatusBar
from ui.toolbar_manager import ToolbarManager

class MainWindow:
    """Main application window implementation."""
    
    def __init__(self, service_container: ServiceContainer):
        self.service_container = service_container
        self.event_bus: EventBus = service_container.get(EventBus)
        self.config: Config = service_container.get(Config)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("NOIR UI")
        self._setup_window()
        
        # Initialize managers
        self.canvas_manager = CanvasManager(
            self.event_bus,
            self.config,
            self.service_container.get('selection_service')
        )
        self.panel_manager = PanelManager(
            self.root,
            self.event_bus,
            self.config
        )
        self.toolbar_manager = ToolbarManager(
            self.root,
            self.event_bus,
            self.config
        )
        self.status_bar = StatusBar(
            self.root,
            self.event_bus,
            self.config
        )
        
        self._setup_layout()
        self._setup_event_handlers()
    
    def _setup_window(self):
        """Set up the main window properties."""
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
    
    def _setup_layout(self):
        """Set up the main window layout."""
        # Toolbar at the top
        self.toolbar_manager.get_widget().grid(
            row=0, column=0, columnspan=3, sticky="ew"
        )
        
        # Left panel
        self.panel_manager.get_left_panel().grid(
            row=1, column=0, sticky="nsew"
        )
        
        # Canvas in the center
        self.panel_manager.get_canvas_panel().grid(
            row=1, column=1, sticky="nsew"
        )
        
        # Right panel
        self.panel_manager.get_right_panel().grid(
            row=1, column=2, sticky="nsew"
        )
        
        # Status bar at the bottom
        self.status_bar.get_widget().grid(
            row=2, column=0, columnspan=3, sticky="ew"
        )
    
    def _setup_event_handlers(self):
        """Set up event handlers for the main window."""
        self.event_bus.subscribe(
            EventType.STATE_CHANGED,
            self._handle_state_changed
        )
        
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _handle_state_changed(self, event):
        """Handle application state changes."""
        # Update window title if project changes
        if 'project_name' in event.data:
            self.root.title(f"NOIR UI - {event.data['project_name']}")
    
    def _on_close(self):
        """Handle window close event."""
        # TODO: Check for unsaved changes
        self.root.quit()
    
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
