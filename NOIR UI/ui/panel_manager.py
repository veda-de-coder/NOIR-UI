"""
Panel management implementation.
"""
import tkinter as tk
from tkinter import ttk
import time
from typing import Dict, Any
from core.event_bus import EventBus, EventType
from core.config import Config

class PanelManager:
    """Manages UI panels and their layout with optimized loading."""
    
    def __init__(self, parent: tk.Widget, event_bus: EventBus, config: Config):
        self.parent = parent
        self.event_bus = event_bus
        self.config = config
        
        # Lazy loading flags
        self._left_panel_loaded = False
        self._right_panel_loaded = False
        
        # Widget caching
        self._property_widgets: Dict[str, ttk.Widget] = {}
        self._component_tree_items: Dict[str, str] = {}
        
        # Update throttling
        self._property_update_scheduled = False
        self._last_update_time = 0
        self._update_throttle = 1/30  # 30 updates per second max
        
        self._create_panels()
        self._setup_event_handlers()
    
    def _create_panels(self):
        """Create all panels."""
        # Left panel for component library
        self.left_panel = ttk.Frame(self.parent)
        self._setup_left_panel()
        
        # Center panel for canvas
        self.canvas_panel = ttk.Frame(self.parent)
        self._setup_canvas_panel()
        
        # Right panel for properties
        self.right_panel = ttk.Frame(self.parent)
        self._setup_right_panel()
    
    def _setup_left_panel(self):
        """Set up the left panel with component library."""
        # Component library
        self.component_tree = ttk.Treeview(self.left_panel)
        self.component_tree.pack(fill=tk.BOTH, expand=True)
        
        # Search box
        search_frame = ttk.Frame(self.left_panel)
        search_frame.pack(fill=tk.X)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_components)
        
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var
        )
        search_entry.pack(fill=tk.X, padx=5, pady=5)
    
    def _setup_canvas_panel(self):
        """Set up the center panel with canvas."""
        self.canvas = tk.Canvas(
            self.canvas_panel,
            bg=self.config.ui.theme['background']
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas events
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self._on_canvas_scroll)
    
    def _setup_right_panel(self):
        """Set up the right panel with optimized properties editor."""
        if not self._right_panel_loaded:
            # Properties notebook
            self.properties_notebook = ttk.Notebook(self.right_panel)
            self.properties_notebook.pack(fill=tk.BOTH, expand=True)
            
            # Properties page
            self.properties_frame = ttk.Frame(self.properties_notebook)
            self.properties_notebook.add(
                self.properties_frame,
                text="Properties"
            )
            
            # Styles page
            self.styles_frame = ttk.Frame(self.properties_notebook)
            self.properties_notebook.add(
                self.styles_frame,
                text="Styles"
            )
            
            self._right_panel_loaded = True
    
    def _update_properties_throttled(self, component):
        """Update properties panel with throttling."""
        current_time = time.time()
        if (not self._property_update_scheduled and 
            current_time - self._last_update_time >= self._update_throttle):
            self._property_update_scheduled = True
            self.parent.after(int(self._update_throttle * 1000), 
                            lambda: self._do_update_properties(component))
    
    def _do_update_properties(self, component):
        """Perform the actual properties update."""
        # Clear schedule flag
        self._property_update_scheduled = False
        self._last_update_time = time.time()
        
        # Only update changed properties
        current_props = {
            name: widget.get() for name, widget in self._property_widgets.items()
            if hasattr(widget, 'get')
        }
        
        for name, value in component.properties.items():
            if name not in self._property_widgets:
                # Create new widget
                widget = self._create_property_widget(name, value)
                self._property_widgets[name] = widget
            elif str(value) != current_props.get(name, ''):
                # Update existing widget only if value changed
                widget = self._property_widgets[name]
                if hasattr(widget, 'set'):
                    widget.set(value)
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        self.event_bus.subscribe(
            EventType.SELECTION_CHANGED,
            self._handle_selection_changed
        )
        self.event_bus.subscribe(
            EventType.COMPONENT_CREATED,
            self._handle_component_created
        )
    
    def get_left_panel(self) -> ttk.Frame:
        """Get the left panel widget."""
        return self.left_panel
    
    def get_canvas_panel(self) -> ttk.Frame:
        """Get the canvas panel widget."""
        return self.canvas_panel
    
    def get_right_panel(self) -> ttk.Frame:
        """Get the right panel widget."""
        return self.right_panel
    
    def _filter_components(self, *args):
        """Filter component library based on search text."""
        search_text = self.search_var.get().lower()
        
        # Clear existing items but keep the root
        for item in self.component_tree.get_children():
            self.component_tree.delete(item)
        
        # Get all available component types from config
        component_types = self.config.get('component_library', {}).get('types', [])
        
        # Filter and add matching components
        for comp_type in component_types:
            type_name = comp_type.get('name', '')
            type_icon = comp_type.get('icon', '')
            
            # Check if search text matches component name or tags
            if (search_text in type_name.lower() or 
                any(search_text in tag.lower() for tag in comp_type.get('tags', []))):
                
                item_id = self.component_tree.insert(
                    '', 'end', 
                    text=type_name,
                    values=(comp_type.get('description', ''), 
                            comp_type.get('category', '')),
                    image=type_icon,
                    tags=('component',)
                )
                
                # Store mapping from tree item to component type
                self._component_tree_items[item_id] = comp_type['id']


    def _on_canvas_click(self, event):
        """Handle canvas click events with selection logic."""
        canvas_x, canvas_y = self.canvas_manager.screen_to_canvas(event.x, event.y)
        
        # Get component at clicked position (implement this in CanvasManager)
        clicked_component = self.canvas_manager.get_component_at(canvas_x, canvas_y)
        
        if clicked_component:
            # Handle selection with modifier keys
            if event.state & 0x0001:  # Shift key
                self.selection_service.toggle_selection(clicked_component.id)
            elif event.state & 0x0004:  # Ctrl key
                self.selection_service.add_to_selection(clicked_component.id)
            else:
                self.selection_service.set_selection(clicked_component.id)
        else:
            # Clicked on empty space - clear selection
            if not (event.state & (0x0001 | 0x0004)):  # No modifier keys
                self.selection_service.clear_selection()

    def _on_canvas_drag(self, event):
        """Handle canvas drag events for moving components."""
        if not hasattr(self, '_drag_start'):
            self._drag_start = (event.x, event.y)
            return
        
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._drag_start = (event.x, event.y)
        
        # Move selected components
        for comp_id in self.selection_service.get_selected_components():
            component = self.project_service.get_component(comp_id)
            if component:
                # Update component position (implement in Component model)
                component.move_by(dx, dy)
        
        # Update canvas
        self.canvas_manager.mark_dirty_region(
            event.x - abs(dx), event.y - abs(dy),
            event.x + abs(dx), event.y + abs(dy)
        )

    def _on_canvas_scroll(self, event):
        """Handle canvas scroll events for zooming."""
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        
        # Get canvas coordinates under mouse
        canvas_x, canvas_y = self.canvas_manager.screen_to_canvas(event.x, event.y)
        
        # Apply zoom
        if event.delta > 0:
            self.canvas_manager.zoom_in_at(canvas_x, canvas_y)
        else:
            self.canvas_manager.zoom_out_at(canvas_x, canvas_y)

    def _handle_selection_changed(self, event):
        """Update properties panel with selected component's properties."""
        selected_ids = event.data.get('selected', [])
        
        # Clear existing properties
        for widget in self._property_widgets.values():
            widget.destroy()
        self._property_widgets.clear()
        
        if len(selected_ids) == 1:
            # Single selection - show all properties
            component = self.project_service.get_component(selected_ids[0])
            if component:
                row = 0
                for prop_name, prop_value in component.properties.items():
                    label = ttk.Label(self.properties_frame, text=prop_name)
                    label.grid(row=row, column=0, sticky='w')
                    
                    if isinstance(prop_value, bool):
                        widget = ttk.Checkbutton(
                            self.properties_frame,
                            variable=tk.BooleanVar(value=prop_value)
                        )
                    elif isinstance(prop_value, (int, float)):
                        widget = ttk.Spinbox(
                            self.properties_frame,
                            from_=0, to=100,
                            textvariable=tk.DoubleVar(value=prop_value)
                        )
                    else:
                        widget = ttk.Entry(
                            self.properties_frame,
                            textvariable=tk.StringVar(value=str(prop_value))
                        )
                    
                    widget.grid(row=row, column=1, sticky='ew')
                    self._property_widgets[prop_name] = widget
                    row += 1
        elif len(selected_ids) > 1:
            # Multi-selection - show common properties
            common_props = self._get_common_properties(selected_ids)
            # ... similar widget creation for common properties ...

    def _handle_component_created(self, event):
        """Update component library with new component type."""
        component_id = event.data.get('component_id')
        component = self.project_service.get_component(component_id)
        
        if component and component.type not in self._component_tree_items.values():
            # Add new component type to library
            item_id = self.component_tree.insert(
                '', 'end',
                text=component.type,
                values=('User-defined component', 'Custom'),
                tags=('component',)
            )
            self._component_tree_items[item_id] = component.type