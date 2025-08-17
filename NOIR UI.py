import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import uuid
import webbrowser
import tempfile
from datetime import datetime
import threading
import base64

@dataclass
class UIComponent:
    id: str
    type: str
    x: int
    y: int
    width: int
    height: int
    properties: Dict[str, Any]
    styles: Dict[str, str]
    children: List[str] = None
    z_index: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class ProjectState:
    components: Dict[str, UIComponent]
    timestamp: str
    description: str = ""

class NoirUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NoirUI - Professional Low-Code UI Designer")
        self.root.geometry("1600x1000")
        self.root.state('zoomed')  # Maximize on Windows
        
        # Application state
        self.components = {}
        self.selected_component = None
        self.canvas_width = 800
        self.canvas_height = 600
        self.current_view = "desktop"  # desktop, tablet, mobile
        self.undo_stack = []
        self.redo_stack = []
        self.project_file = None
        self.is_modified = False
        self.zoom_level = 1.0
        
        # Drag state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
        # Grid and snap
        self.grid_enabled = True
        self.snap_to_grid = True
        self.grid_size = 10
        
        # Collaboration
        self.collaboration_mode = False
        self.user_color = "#ff6b6b"
        
        # Performance tracking
        self.render_time = 0
        self.component_count = 0
        
        # Predefined templates and components
        self.templates = self._load_templates()
        self.component_library = self._load_component_library()
        self.color_palettes = self._load_color_palettes()
        self.current_theme = "default"
        
        # AI Assistant (mock implementation)
        self.ai_suggestions = []
        
        self._setup_ui()
        self._setup_shortcuts()
        
    def _setup_ui(self):
        # Create main menu
        self._create_menu()
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top toolbar
        self._create_enhanced_toolbar(main_frame)
        
        # Status bar
        self._create_status_bar(main_frame)
        
        # Main content area with paned windows
        self._create_main_content(main_frame)
        
        # Initial render
        self.render_canvas()
        
    def _create_menu(self):
        """Create comprehensive menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Import Template", command=self.import_template)
        file_menu.add_command(label="Export HTML", command=self.export_html)
        file_menu.add_command(label="Export React", command=self.export_react)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self.copy_component, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste_component, accelerator="Ctrl+V")
        edit_menu.add_command(label="Delete", command=self.delete_selected_component, accelerator="Del")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=lambda: self.zoom_canvas(1.2), accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=lambda: self.zoom_canvas(0.8), accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=lambda: self.zoom_canvas(1.0, reset=True), accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", command=self.toggle_grid)
        view_menu.add_checkbutton(label="Snap to Grid", command=self.toggle_snap)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="AI Design Assistant", command=self.show_ai_assistant)
        tools_menu.add_command(label="Accessibility Checker", command=self.check_accessibility)
        tools_menu.add_command(label="Performance Audit", command=self.performance_audit)
        tools_menu.add_separator()
        tools_menu.add_command(label="Component Library", command=self.show_component_library)
        tools_menu.add_command(label="Style Guide", command=self.show_style_guide)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Tutorial", command=self.show_tutorial)
        help_menu.add_command(label="Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
        
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            '<Control-n>': self.new_project,
            '<Control-o>': self.open_project,
            '<Control-s>': self.save_project,
            '<Control-Shift-S>': self.save_project_as,
            '<Control-z>': self.undo,
            '<Control-y>': self.redo,
            '<Control-c>': self.copy_component,
            '<Control-v>': self.paste_component,
            '<Delete>': self.delete_selected_component,
            '<Control-a>': self.select_all,
            '<Control-plus>': lambda: self.zoom_canvas(1.2),
            '<Control-minus>': lambda: self.zoom_canvas(0.8),
            '<Control-0>': lambda: self.zoom_canvas(1.0, reset=True),
            '<F5>': self.preview_ui,
            '<Control-d>': self.duplicate_component,
            '<Control-g>': self.group_components,
            '<Escape>': self.deselect_all,
        }
        
        for key, command in shortcuts.items():
            self.root.bind(key, lambda e, cmd=command: cmd())
            
    def _create_enhanced_toolbar(self, parent):
        """Create comprehensive toolbar with all tools"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Main toolbar
        toolbar = ttk.Frame(toolbar_frame)
        toolbar.pack(fill=tk.X)
        
        # File operations
        file_frame = ttk.LabelFrame(toolbar, text="File", padding=5)
        file_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(file_frame, text="New", command=self.new_project, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(file_frame, text="Open", command=self.open_project, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(file_frame, text="Save", command=self.save_project, width=8).pack(side=tk.LEFT, padx=1)
        
        # Edit operations
        edit_frame = ttk.LabelFrame(toolbar, text="Edit", padding=5)
        edit_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(edit_frame, text="Undo", command=self.undo, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(edit_frame, text="Redo", command=self.redo, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(edit_frame, text="Copy", command=self.copy_component, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(edit_frame, text="Paste", command=self.paste_component, width=8).pack(side=tk.LEFT, padx=1)
        
        # View controls
        view_frame = ttk.LabelFrame(toolbar, text="View", padding=5)
        view_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(view_frame, text="Device:").pack(side=tk.LEFT, padx=2)
        self.view_var = tk.StringVar(value="desktop")
        view_combo = ttk.Combobox(view_frame, textvariable=self.view_var, 
                                 values=["desktop", "tablet", "mobile"], 
                                 state="readonly", width=10)
        view_combo.pack(side=tk.LEFT, padx=2)
        view_combo.bind('<<ComboboxSelected>>', lambda e: self.change_view(self.view_var.get()))
        
        # Zoom controls
        ttk.Label(view_frame, text="Zoom:").pack(side=tk.LEFT, padx=(10,2))
        self.zoom_var = tk.StringVar(value="100%")
        zoom_combo = ttk.Combobox(view_frame, textvariable=self.zoom_var,
                                 values=["25%", "50%", "75%", "100%", "125%", "150%", "200%"],
                                 state="readonly", width=8)
        zoom_combo.pack(side=tk.LEFT, padx=2)
        zoom_combo.bind('<<ComboboxSelected>>', self._on_zoom_change)
        
        # AI & Tools
        ai_frame = ttk.LabelFrame(toolbar, text="AI Tools", padding=5)
        ai_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(ai_frame, text="AI Suggest", command=self.ai_suggest_layout, width=10).pack(side=tk.LEFT, padx=1)
        ttk.Button(ai_frame, text="Auto Align", command=self.auto_align_components, width=10).pack(side=tk.LEFT, padx=1)
        
        # Export & Preview
        export_frame = ttk.LabelFrame(toolbar, text="Export", padding=5)
        export_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(export_frame, text="Preview", command=self.preview_ui, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(export_frame, text="HTML", command=self.export_html, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(export_frame, text="React", command=self.export_react, width=8).pack(side=tk.LEFT, padx=1)
        
        # Collaboration (if enabled)
        if self.collaboration_mode:
            collab_frame = ttk.LabelFrame(toolbar, text="Collaborate", padding=5)
            collab_frame.pack(side=tk.RIGHT, padx=2)
            
            ttk.Button(collab_frame, text="Share", command=self.share_project, width=8).pack(side=tk.LEFT, padx=1)
            ttk.Button(collab_frame, text="Comments", command=self.show_comments, width=8).pack(side=tk.LEFT, padx=1)
        
        # Second toolbar row for additional controls
        toolbar2 = ttk.Frame(toolbar_frame)
        toolbar2.pack(fill=tk.X, pady=(5,0))
        
        # Grid controls
        grid_frame = ttk.Frame(toolbar2)
        grid_frame.pack(side=tk.LEFT)
        
        self.grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(grid_frame, text="Grid", variable=self.grid_var, 
                       command=self.toggle_grid).pack(side=tk.LEFT, padx=2)
        
        self.snap_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(grid_frame, text="Snap", variable=self.snap_var,
                       command=self.toggle_snap).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(grid_frame, text="Size:").pack(side=tk.LEFT, padx=(10,2))
        self.grid_size_var = tk.IntVar(value=10)
        grid_spin = ttk.Spinbox(grid_frame, from_=5, to=50, textvariable=self.grid_size_var,
                               width=5, command=self._on_grid_size_change)
        grid_spin.pack(side=tk.LEFT, padx=2)
        
    def _create_status_bar(self, parent):
        """Create status bar with useful information"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5,0))
        
        # Left side - general status
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Right side - component info, performance, etc.
        self.info_frame = ttk.Frame(self.status_frame)
        self.info_frame.pack(side=tk.RIGHT)
        
        self.component_count_label = ttk.Label(self.info_frame, text="Components: 0")
        self.component_count_label.pack(side=tk.RIGHT, padx=(0,10))
        
        self.render_time_label = ttk.Label(self.info_frame, text="Render: 0ms")
        self.render_time_label.pack(side=tk.RIGHT, padx=(0,10))
        
        self.canvas_info_label = ttk.Label(self.info_frame, text=f"Canvas: {self.canvas_width}x{self.canvas_height}")
        self.canvas_info_label.pack(side=tk.RIGHT, padx=(0,10))
        
    def _create_main_content(self, parent):
        """Create main content area with paned windows"""
        # Main paned window (horizontal)
        self.main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        
        # Left panel - Components and Templates
        self._create_left_panel()
        
        # Center - Canvas area
        self._create_center_panel()
        
        # Right panel - Properties and Layers
        self._create_right_panel()
        
    def _create_left_panel(self):
        """Create enhanced left panel with components, templates, and AI"""
        left_panel = ttk.Frame(self.main_paned, width=300)
        self.main_paned.add(left_panel, weight=0)
        
        # Notebook for different tabs
        self.left_notebook = ttk.Notebook(left_panel)
        self.left_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Components tab
        self._create_components_tab()
        
        # Templates tab
        self._create_templates_tab()
        
        # Themes tab
        self._create_themes_tab()
        
        # AI Assistant tab
        self._create_ai_tab()
        
    def _create_components_tab(self):
        """Enhanced components tab with categories"""
        comp_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(comp_frame, text="Components")
        
        # Search box
        search_frame = ttk.Frame(comp_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.comp_search_var = tk.StringVar()
        comp_search = ttk.Entry(search_frame, textvariable=self.comp_search_var)
        comp_search.pack(fill=tk.X, padx=(5,0))
        comp_search.bind('<KeyRelease>', self._filter_components)
        
        # Component categories
        categories = {
            "Basic": ["button", "input", "text", "header", "image"],
            "Layout": ["container", "card", "grid", "flex"],
            "Forms": ["form", "checkbox", "radio", "select", "textarea"],
            "Navigation": ["navbar", "breadcrumb", "pagination", "tabs"],
            "Data": ["table", "list", "chart", "progress"]
        }
        
        self.comp_tree = ttk.Treeview(comp_frame)
        self.comp_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        
        # Populate component tree
        for category, components in categories.items():
            cat_id = self.comp_tree.insert('', 'end', text=category)
            for comp_type in components:
                if comp_type in self.component_library:
                    comp_name = self.component_library[comp_type]['name']
                    self.comp_tree.insert(cat_id, 'end', text=comp_name, values=[comp_type])
        
        self.comp_tree.bind('<Double-1>', self._on_component_double_click)
        
    def _create_templates_tab(self):
        """Enhanced templates tab"""
        temp_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(temp_frame, text="Templates")
        
        ttk.Label(temp_frame, text="Quick Start Templates", 
                 font=("Arial", 10, "bold")).pack(pady=5)
        
        # Template preview (simplified)
        self.template_listbox = tk.Listbox(temp_frame)
        self.template_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for template_name in self.templates.keys():
            display_name = template_name.replace('_', ' ').title()
            self.template_listbox.insert(tk.END, display_name)
        
        self.template_listbox.bind('<Double-1>', self._on_template_double_click)
        
        # Template actions
        temp_actions = ttk.Frame(temp_frame)
        temp_actions.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(temp_actions, text="Load Template", 
                  command=self._load_selected_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(temp_actions, text="Save as Template", 
                  command=self.save_as_template).pack(side=tk.RIGHT, padx=2)
        
    def _create_themes_tab(self):
        """Enhanced themes and styling tab"""
        theme_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(theme_frame, text="Themes")
        
        ttk.Label(theme_frame, text="Color Palettes", 
                 font=("Arial", 10, "bold")).pack(pady=5)
        
        # Color palette preview
        for palette_name, colors in self.color_palettes.items():
            palette_frame = ttk.LabelFrame(theme_frame, text=palette_name.title())
            palette_frame.pack(fill=tk.X, padx=5, pady=2)
            
            color_row = ttk.Frame(palette_frame)
            color_row.pack(fill=tk.X, padx=5, pady=5)
            
            for color_name, color_value in colors.items():
                color_btn = tk.Button(color_row, bg=color_value, width=3, height=1,
                                    command=lambda pn=palette_name: self.apply_theme(pn))
                color_btn.pack(side=tk.LEFT, padx=1)
                
        # Custom color picker
        custom_frame = ttk.LabelFrame(theme_frame, text="Custom Colors")
        custom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(custom_frame, text="Pick Primary Color", 
                  command=self.pick_primary_color).pack(fill=tk.X, pady=2)
        ttk.Button(custom_frame, text="Pick Accent Color", 
                  command=self.pick_accent_color).pack(fill=tk.X, pady=2)
        
    def _create_ai_tab(self):
        """AI Assistant tab"""
        ai_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(ai_frame, text="AI Assistant")
        
        ttk.Label(ai_frame, text="AI Design Assistant", 
                 font=("Arial", 10, "bold")).pack(pady=5)
        
        # AI suggestions area
        suggest_frame = ttk.LabelFrame(ai_frame, text="Suggestions")
        suggest_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.ai_text = tk.Text(suggest_frame, height=8, wrap=tk.WORD)
        self.ai_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # AI actions
        ai_actions = ttk.Frame(ai_frame)
        ai_actions.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ai_actions, text="Suggest Layout", 
                  command=self.ai_suggest_layout).pack(fill=tk.X, pady=2)
        ttk.Button(ai_actions, text="Optimize Colors", 
                  command=self.ai_optimize_colors).pack(fill=tk.X, pady=2)
        ttk.Button(ai_actions, text="Improve Accessibility", 
                  command=self.ai_improve_accessibility).pack(fill=tk.X, pady=2)
        
    def _create_center_panel(self):
        """Create enhanced center panel with canvas"""
        center_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(center_panel, weight=1)
        
        # Canvas toolbar
        canvas_toolbar = ttk.Frame(center_panel)
        canvas_toolbar.pack(fill=tk.X, padx=5, pady=(5,0))
        
        ttk.Button(canvas_toolbar, text="Fit to Window", 
                  command=self.fit_canvas_to_window).pack(side=tk.LEFT, padx=2)
        ttk.Button(canvas_toolbar, text="Actual Size", 
                  command=self.reset_canvas_zoom).pack(side=tk.LEFT, padx=2)
        
        # Canvas container with enhanced scrolling
        canvas_container = ttk.Frame(center_panel)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_container, bg="white", 
                               width=self.canvas_width, height=self.canvas_height,
                               scrollregion=(0, 0, 1600, 1200))
        
        h_scroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, 
                                command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, 
                                command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Enhanced canvas events
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<Double-Button-1>", self.canvas_double_click)
        self.canvas.bind("<Button-3>", self.canvas_right_click)  # Right click menu
        self.canvas.bind("<MouseWheel>", self.canvas_mouse_wheel)
        
        # Context menu for canvas
        self.canvas_menu = tk.Menu(self.root, tearoff=0)
        self.canvas_menu.add_command(label="Paste", command=self.paste_component)
        self.canvas_menu.add_command(label="Select All", command=self.select_all)
        self.canvas_menu.add_separator()
        self.canvas_menu.add_command(label="Add Button", command=lambda: self.add_component("button"))
        self.canvas_menu.add_command(label="Add Text", command=lambda: self.add_component("text"))
        self.canvas_menu.add_command(label="Add Container", command=lambda: self.add_component("container"))
        
    def _create_right_panel(self):
        """Create enhanced right panel"""
        right_panel = ttk.Frame(self.main_paned, width=350)
        self.main_paned.add(right_panel, weight=0)
        
        # Right panel notebook
        self.right_notebook = ttk.Notebook(right_panel)
        self.right_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Properties tab
        self._create_properties_tab()
        
        # Layers tab
        self._create_layers_tab()
        
        # History tab
        self._create_history_tab()
        
        # Inspector tab (accessibility, performance)
        self._create_inspector_tab()
        
    def _create_properties_tab(self):
        """Enhanced properties tab"""
        self.props_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.props_frame, text="Properties")
        
        # Component info
        info_frame = ttk.LabelFrame(self.props_frame, text="Component Info")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.comp_info_label = ttk.Label(info_frame, text="No selection")
        self.comp_info_label.pack(pady=5)
        
        # Properties content (scrollable)
        props_canvas = tk.Canvas(self.props_frame)
        props_scrollbar = ttk.Scrollbar(self.props_frame, orient="vertical", command=props_canvas.yview)
        self.props_scrollable_frame = ttk.Frame(props_canvas)
        
        self.props_scrollable_frame.bind(
            "<Configure>",
            lambda e: props_canvas.configure(scrollregion=props_canvas.bbox("all"))
        )
        
        props_canvas.create_window((0, 0), window=self.props_scrollable_frame, anchor="nw")
        props_canvas.configure(yscrollcommand=props_scrollbar.set)
        
        props_canvas.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
        props_scrollbar.pack(side="right", fill="y", pady=5)
        
        self.update_properties_panel()
        
    def _create_layers_tab(self):
        """Create layers/hierarchy tab"""
        layers_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(layers_frame, text="Layers")
        
        ttk.Label(layers_frame, text="Component Layers", 
                 font=("Arial", 10, "bold")).pack(pady=5)
        
        # Layer tree
        self.layers_tree = ttk.Treeview(layers_frame)
        self.layers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Layer controls
        layer_controls = ttk.Frame(layers_frame)
        layer_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(layer_controls, text="▲", width=3,
                  command=self.move_layer_up).pack(side=tk.LEFT, padx=1)
        ttk.Button(layer_controls, text="▼", width=3,
                  command=self.move_layer_down).pack(side=tk.LEFT, padx=1)
        ttk.Button(layer_controls, text="👁", width=3,
                  command=self.toggle_layer_visibility).pack(side=tk.LEFT, padx=1)
        ttk.Button(layer_controls, text="🔒", width=3,
                  command=self.toggle_layer_lock).pack(side=tk.LEFT, padx=1)
        
        self.layers_tree.bind('<ButtonRelease-1>', self._on_layer_select)
        
    def _create_history_tab(self):
        """Create history/undo tab"""
        history_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(history_frame, text="History")
        
        ttk.Label(history_frame, text="Action History", 
                 font=("Arial", 10, "bold")).pack(pady=5)
        
        # History list
        self.history_listbox = tk.Listbox(history_frame)
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(history_controls, text="Revert to Selected", 
                  command=self.revert_to_history).pack(fill=tk.X, pady=2)
        ttk.Button(history_controls, text="Clear History", 
                  command=self.clear_history).pack(fill=tk.X, pady=2)
        
    def _create_inspector_tab(self):
        """Create inspector tab for accessibility and performance"""
        inspector_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(inspector_frame, text="Inspector")
        
        # Accessibility section
        acc_frame = ttk.LabelFrame(inspector_frame, text="Accessibility")
        acc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.acc_text = tk.Text(acc_frame, height=6, wrap=tk.WORD)
        self.acc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(acc_frame, text="Check Accessibility", 
                  command=self.check_accessibility).pack(fill=tk.X, padx=5, pady=2)
        
        # Performance section
        perf_frame = ttk.LabelFrame(inspector_frame, text="Performance")
        perf_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.perf_text = tk.Text(perf_frame, height=6, wrap=tk.WORD)
        self.perf_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(perf_frame, text="Run Performance Audit", 
                  command=self.performance_audit).pack(fill=tk.X, padx=5, pady=2)
        
    # Enhanced component management methods
    def _load_templates(self):
        """Load enhanced templates with more variety"""
        return {
            "landing_page": {
                "name": "Landing Page",
                "description": "Modern landing page with hero section",
                "components": [
                    {"type": "navbar", "x": 0, "y": 0, "width": 800, "height": 60},
                    {"type": "header", "x": 50, "y": 80, "width": 700, "height": 120, 
                     "properties": {"content": "Welcome to Our Platform", "level": "h1"}},
                    {"type": "text", "x": 50, "y": 220, "width": 700, "height": 80,
                     "properties": {"content": "Build amazing applications with our low-code platform"}},
                    {"type": "button", "x": 350, "y": 320, "width": 150, "height": 50,
                     "properties": {"text": "Get Started"}},
                    {"type": "card", "x": 50, "y": 400, "width": 200, "height": 150},
                    {"type": "card", "x": 300, "y": 400, "width": 200, "height": 150},
                    {"type": "card", "x": 550, "y": 400, "width": 200, "height": 150}
                ]
            },
            "dashboard": {
                "name": "Admin Dashboard",
                "description": "Professional admin dashboard layout",
                "components": [
                    {"type": "navbar", "x": 0, "y": 0, "width": 800, "height": 60},
                    {"type": "sidebar", "x": 0, "y": 60, "width": 200, "height": 540},
                    {"type": "header", "x": 220, "y": 80, "width": 560, "height": 60,
                     "properties": {"content": "Dashboard", "level": "h2"}},
                    {"type": "card", "x": 220, "y": 160, "width": 180, "height": 120,
                     "properties": {"title": "Total Users", "content": "1,234"}},
                    {"type": "card", "x": 420, "y": 160, "width": 180, "height": 120,
                     "properties": {"title": "Revenue", "content": "$12,345"}},
                    {"type": "card", "x": 620, "y": 160, "width": 160, "height": 120,
                     "properties": {"title": "Orders", "content": "856"}},
                    {"type": "chart", "x": 220, "y": 300, "width": 560, "height": 280}
                ]
            },
            "form": {
                "name": "Contact Form",
                "description": "Clean contact form with validation",
                "components": [
                    {"type": "header", "x": 200, "y": 50, "width": 400, "height": 60,
                     "properties": {"content": "Contact Us", "level": "h2"}},
                    {"type": "input", "x": 200, "y": 130, "width": 400, "height": 40,
                     "properties": {"placeholder": "Your Name", "type": "text"}},
                    {"type": "input", "x": 200, "y": 180, "width": 400, "height": 40,
                     "properties": {"placeholder": "Email Address", "type": "email"}},
                    {"type": "input", "x": 200, "y": 230, "width": 400, "height": 40,
                     "properties": {"placeholder": "Phone Number", "type": "tel"}},
                    {"type": "textarea", "x": 200, "y": 280, "width": 400, "height": 120,
                     "properties": {"placeholder": "Your Message"}},
                    {"type": "button", "x": 350, "y": 420, "width": 100, "height": 40,
                     "properties": {"text": "Send Message"}}
                ]
            },
            "blog": {
                "name": "Blog Layout",
                "description": "Modern blog homepage layout",
                "components": [
                    {"type": "navbar", "x": 0, "y": 0, "width": 800, "height": 60},
                    {"type": "header", "x": 50, "y": 80, "width": 500, "height": 80,
                     "properties": {"content": "Latest Articles", "level": "h1"}},
                    {"type": "card", "x": 50, "y": 180, "width": 350, "height": 200,
                     "properties": {"title": "Featured Article", "content": "Lorem ipsum..."}},
                    {"type": "card", "x": 420, "y": 180, "width": 330, "height": 95,
                     "properties": {"title": "Quick Read", "content": "Short article..."}},
                    {"type": "card", "x": 420, "y": 285, "width": 330, "height": 95,
                     "properties": {"title": "Tech News", "content": "Latest updates..."}},
                    {"type": "sidebar", "x": 600, "y": 400, "width": 200, "height": 200}
                ]
            },
            "ecommerce": {
                "name": "E-commerce Product",
                "description": "Product page layout for online store",
                "components": [
                    {"type": "navbar", "x": 0, "y": 0, "width": 800, "height": 60},
                    {"type": "image", "x": 50, "y": 80, "width": 350, "height": 350,
                     "properties": {"alt": "Product Image"}},
                    {"type": "header", "x": 420, "y": 80, "width": 330, "height": 60,
                     "properties": {"content": "Product Name", "level": "h1"}},
                    {"type": "text", "x": 420, "y": 150, "width": 330, "height": 40,
                     "properties": {"content": "$99.99", "tag": "span"}},
                    {"type": "text", "x": 420, "y": 200, "width": 330, "height": 120,
                     "properties": {"content": "Product description..."}},
                    {"type": "button", "x": 420, "y": 340, "width": 120, "height": 40,
                     "properties": {"text": "Add to Cart"}},
                    {"type": "button", "x": 550, "y": 340, "width": 120, "height": 40,
                     "properties": {"text": "Buy Now"}}
                ]
            }
        }
    
    def _load_component_library(self):
        """Enhanced component library with more components"""
        return {
            "button": {
                "name": "Button",
                "category": "Basic",
                "default_props": {"text": "Click Me", "disabled": False, "type": "button"},
                "default_styles": {"background": "#007bff", "color": "white", "border": "none", 
                                 "border-radius": "6px", "padding": "8px 16px", "font-size": "14px", "cursor": "pointer"}
            },
            "input": {
                "name": "Text Input",
                "category": "Forms",
                "default_props": {"placeholder": "Enter text...", "type": "text", "required": False},
                "default_styles": {"border": "2px solid #e1e5e9", "padding": "8px 12px", "border-radius": "6px",
                                 "font-size": "14px", "width": "100%"}
            },
            "textarea": {
                "name": "Text Area",
                "category": "Forms",
                "default_props": {"placeholder": "Enter your message...", "rows": 4, "cols": 50},
                "default_styles": {"border": "2px solid #e1e5e9", "padding": "8px 12px", "border-radius": "6px",
                                 "font-size": "14px", "resize": "vertical"}
            },
            "text": {
                "name": "Text",
                "category": "Basic",
                "default_props": {"content": "Sample Text", "tag": "p"},
                "default_styles": {"font-family": "'Segoe UI', Arial, sans-serif", "font-size": "16px", 
                                 "color": "#333333", "line-height": "1.5"}
            },
            "header": {
                "name": "Header",
                "category": "Basic",
                "default_props": {"content": "Header Text", "level": "h1"},
                "default_styles": {"font-family": "'Segoe UI', Arial, sans-serif", "font-size": "32px", 
                                 "font-weight": "bold", "color": "#1a1a1a", "margin": "0 0 16px 0"}
            },
            "image": {
                "name": "Image",
                "category": "Media",
                "default_props": {"src": "https://via.placeholder.com/300x200", "alt": "Placeholder Image"},
                "default_styles": {"border": "none", "border-radius": "8px", "max-width": "100%", "height": "auto"}
            },
            "card": {
                "name": "Card",
                "category": "Layout",
                "default_props": {"title": "Card Title", "content": "Card content goes here..."},
                "default_styles": {"background": "white", "border": "1px solid #e1e5e9", "border-radius": "12px", 
                                 "padding": "20px", "box-shadow": "0 2px 8px rgba(0,0,0,0.1)"}
            },
            "container": {
                "name": "Container",
                "category": "Layout",
                "default_props": {"flex_direction": "column", "align_items": "stretch"},
                "default_styles": {"background": "transparent", "border": "2px dashed #cbd5e0", 
                                 "border-radius": "8px", "min-height": "100px", "padding": "16px"}
            },
            "navbar": {
                "name": "Navigation Bar",
                "category": "Navigation",
                "default_props": {"brand": "Brand", "links": ["Home", "About", "Contact"]},
                "default_styles": {"background": "#ffffff", "border-bottom": "1px solid #e1e5e9", 
                                 "padding": "12px 24px", "display": "flex", "justify-content": "space-between"}
            },
            "sidebar": {
                "name": "Sidebar",
                "category": "Layout",
                "default_props": {"width": "250px", "items": ["Dashboard", "Users", "Settings"]},
                "default_styles": {"background": "#f8f9fa", "border-right": "1px solid #e1e5e9", 
                                 "padding": "20px", "height": "100%"}
            },
            "form": {
                "name": "Form",
                "category": "Forms",
                "default_props": {"method": "POST", "action": "#"},
                "default_styles": {"background": "white", "padding": "24px", "border-radius": "12px",
                                 "box-shadow": "0 4px 12px rgba(0,0,0,0.1)"}
            },
            "select": {
                "name": "Select Dropdown",
                "category": "Forms",
                "default_props": {"options": ["Option 1", "Option 2", "Option 3"], "multiple": False},
                "default_styles": {"border": "2px solid #e1e5e9", "padding": "8px 12px", "border-radius": "6px",
                                 "font-size": "14px", "background": "white"}
            },
            "checkbox": {
                "name": "Checkbox",
                "category": "Forms",
                "default_props": {"label": "Check me", "checked": False, "value": "checkbox1"},
                "default_styles": {"margin": "8px 0", "display": "flex", "align-items": "center", "gap": "8px"}
            },
            "radio": {
                "name": "Radio Button",
                "category": "Forms",
                "default_props": {"label": "Select me", "name": "radio1", "value": "option1"},
                "default_styles": {"margin": "8px 0", "display": "flex", "align-items": "center", "gap": "8px"}
            },
            "chart": {
                "name": "Chart",
                "category": "Data",
                "default_props": {"type": "bar", "data": "[10, 20, 30, 40]", "labels": "['A', 'B', 'C', 'D']"},
                "default_styles": {"background": "white", "border": "1px solid #e1e5e9", "border-radius": "8px",
                                 "padding": "16px"}
            },
            "table": {
                "name": "Table",
                "category": "Data",
                "default_props": {"headers": ["Name", "Email", "Role"], "rows": 3},
                "default_styles": {"width": "100%", "border-collapse": "collapse", "border": "1px solid #e1e5e9"}
            },
            "tabs": {
                "name": "Tabs",
                "category": "Navigation",
                "default_props": {"tabs": ["Tab 1", "Tab 2", "Tab 3"], "active": 0},
                "default_styles": {"border-bottom": "1px solid #e1e5e9", "background": "white"}
            },
            "progress": {
                "name": "Progress Bar",
                "category": "Feedback",
                "default_props": {"value": 50, "max": 100, "label": "Progress"},
                "default_styles": {"width": "100%", "height": "8px", "background": "#e1e5e9", "border-radius": "4px"}
            },
            "modal": {
                "name": "Modal",
                "category": "Overlay",
                "default_props": {"title": "Modal Title", "content": "Modal content...", "visible": False},
                "default_styles": {"background": "white", "border-radius": "12px", "padding": "24px",
                                 "box-shadow": "0 20px 40px rgba(0,0,0,0.3)"}
            },
            "grid": {
                "name": "Grid Layout",
                "category": "Layout",
                "default_props": {"columns": 3, "gap": "16px"},
                "default_styles": {"display": "grid", "gap": "16px", "grid-template-columns": "repeat(3, 1fr)"}
            },
            "flex": {
                "name": "Flex Container",
                "category": "Layout",
                "default_props": {"direction": "row", "justify": "flex-start", "align": "stretch"},
                "default_styles": {"display": "flex", "gap": "8px", "flex-wrap": "wrap"}
            }
        }
    
    def _load_color_palettes(self):
        """Enhanced color palettes with more variety"""
        return {
            "default": {
                "primary": "#007bff",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "light": "#f8f9fa",
                "dark": "#343a40"
            },
            "modern_blue": {
                "primary": "#3b82f6",
                "secondary": "#64748b",
                "success": "#10b981",
                "danger": "#ef4444",
                "warning": "#f59e0b",
                "info": "#06b6d4",
                "light": "#f1f5f9",
                "dark": "#1e293b"
            },
            "purple_gradient": {
                "primary": "#8b5cf6",
                "secondary": "#a78bfa",
                "success": "#34d399",
                "danger": "#f87171",
                "warning": "#fbbf24",
                "info": "#60a5fa",
                "light": "#faf5ff",
                "dark": "#581c87"
            },
            "warm_sunset": {
                "primary": "#f97316",
                "secondary": "#fb923c",
                "success": "#65a30d",
                "danger": "#dc2626",
                "warning": "#eab308",
                "info": "#0ea5e9",
                "light": "#fff7ed",
                "dark": "#9a3412"
            },
            "cool_mint": {
                "primary": "#059669",
                "secondary": "#047857",
                "success": "#10b981",
                "danger": "#e11d48",
                "warning": "#d97706",
                "info": "#0891b2",
                "light": "#ecfdf5",
                "dark": "#064e3b"
            },
            "dark_theme": {
                "primary": "#6366f1",
                "secondary": "#4f46e5",
                "success": "#22c55e",
                "danger": "#ef4444",
                "warning": "#eab308",
                "info": "#3b82f6",
                "light": "#374151",
                "dark": "#111827"
            },
            "pastel_dream": {
                "primary": "#ec4899",
                "secondary": "#8b5cf6",
                "success": "#34d399",
                "danger": "#fca5a5",
                "warning": "#fde68a",
                "info": "#93c5fd",
                "light": "#fdf2f8",
                "dark": "#831843"
            }
        }

    # Core functionality methods
    def add_component(self, comp_type, x=None, y=None):
        """Add a new component to the canvas with enhanced positioning"""
        if comp_type not in self.component_library:
            messagebox.showerror("Error", f"Unknown component type: {comp_type}")
            return
            
        comp_data = self.component_library[comp_type]
        
        # Smart positioning - avoid overlaps
        if x is None or y is None:
            x, y = self._find_best_position(comp_type)
        
        # Snap to grid if enabled
        if self.snap_to_grid:
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size
        
        # Determine default size based on component type
        default_sizes = {
            "button": (120, 40),
            "input": (200, 40),
            "textarea": (300, 120),
            "text": (200, 30),
            "header": (300, 60),
            "image": (200, 150),
            "card": (250, 180),
            "container": (300, 200),
            "navbar": (self.canvas_width, 60),
            "sidebar": (200, 400),
            "form": (400, 300),
            "table": (400, 200),
            "chart": (350, 250)
        }
        
        width, height = default_sizes.get(comp_type, (200, 100))
        
        component = UIComponent(
            id=str(uuid.uuid4()),
            type=comp_type,
            x=x,
            y=y,
            width=width,
            height=height,
            properties=comp_data.get("default_props", {}).copy(),
            styles=comp_data.get("default_styles", {}).copy(),
            z_index=len(self.components)
        )
        
        self.save_state(f"Added {comp_data['name']}")
        self.components[component.id] = component
        self.selected_component = component.id
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        
        # Update status
        self.update_status(f"Added {comp_data['name']} component")
        
    def _find_best_position(self, comp_type):
        """Find the best position for a new component to avoid overlaps"""
        start_x, start_y = 50, 50
        grid_size = 20
        
        # Get existing component bounds
        occupied = []
        for comp in self.components.values():
            occupied.append((comp.x, comp.y, comp.x + comp.width, comp.y + comp.height))
        
        # Try positions in a grid pattern
        for row in range(0, self.canvas_height // grid_size):
            for col in range(0, self.canvas_width // grid_size):
                x = col * grid_size + start_x
                y = row * grid_size + start_y
                
                # Check if this position overlaps with existing components
                overlaps = False
                test_width, test_height = 200, 100  # Default test size
                
                for ox, oy, ox2, oy2 in occupied:
                    if not (x + test_width < ox or x > ox2 or y + test_height < oy or y > oy2):
                        overlaps = True
                        break
                
                if not overlaps:
                    return x, y
        
        # If no free space found, use offset from existing components
        return start_x + len(self.components) * 20, start_y + len(self.components) * 20
    
    # Enhanced event handlers
    def canvas_click(self, event):
        """Enhanced canvas click with multi-selection support"""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Find clicked component (top-most first)
        clicked_comp = None
        max_z = -1
        
        for comp_id, comp in self.components.items():
            if (comp.x <= x <= comp.x + comp.width and 
                comp.y <= y <= comp.y + comp.height):
                if comp.z_index > max_z:
                    max_z = comp.z_index
                    clicked_comp = comp_id
        
        # Handle selection
        if event.state & 0x1:  # Ctrl key held
            if clicked_comp:
                if isinstance(self.selected_component, list):
                    if clicked_comp in self.selected_component:
                        self.selected_component.remove(clicked_comp)
                    else:
                        self.selected_component.append(clicked_comp)
                else:
                    if self.selected_component == clicked_comp:
                        self.selected_component = None
                    else:
                        self.selected_component = [self.selected_component, clicked_comp] if self.selected_component else [clicked_comp]
        else:
            self.selected_component = clicked_comp
        
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        
        # Store drag start position
        if self.selected_component:
            selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
            if selected_comps and selected_comps[0] in self.components:
                first_comp = self.components[selected_comps[0]]
                self.drag_start_x = x - first_comp.x
                self.drag_start_y = y - first_comp.y
    
    def canvas_drag(self, event):
        """Enhanced dragging with multi-component support"""
        if not self.selected_component:
            return
            
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        for comp_id in selected_comps:
            if comp_id not in self.components:
                continue
                
            comp = self.components[comp_id]
            new_x = max(0, x - self.drag_start_x)
            new_y = max(0, y - self.drag_start_y)
            
            # Snap to grid if enabled
            if self.snap_to_grid:
                new_x = round(new_x / self.grid_size) * self.grid_size
                new_y = round(new_y / self.grid_size) * self.grid_size
            
            comp.x = new_x
            comp.y = new_y
        
        self.is_dragging = True
        self.render_canvas()
    
    def canvas_double_click(self, event):
        """Handle double-click for quick editing"""
        if not self.selected_component or isinstance(self.selected_component, list):
            return
            
        comp = self.components[self.selected_component]
        
        # Quick edit for text-based components
        if comp.type in ["text", "header", "button"]:
            current_text = comp.properties.get("content" if comp.type in ["text", "header"] else "text", "")
            new_text = simpledialog.askstring("Quick Edit", f"Edit {comp.type} text:", initialvalue=current_text)
            if new_text is not None:
                self.save_state(f"Quick edit {comp.type}")
                if comp.type in ["text", "header"]:
                    comp.properties["content"] = new_text
                else:
                    comp.properties["text"] = new_text
                self.render_canvas()
                self.update_properties_panel()
    
    def canvas_right_click(self, event):
        """Show context menu on right click"""
        try:
            self.canvas_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.canvas_menu.grab_release()
    
    def canvas_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        if event.state & 0x4:  # Ctrl key held
            if event.delta > 0:
                self.zoom_canvas(1.1)
            else:
                self.zoom_canvas(0.9)
    
    # Rendering methods
    def render_canvas(self):
        """Enhanced canvas rendering with performance tracking"""
        start_time = datetime.now()
        
        self.canvas.delete("all")
        
        # Draw grid if enabled
        if self.grid_enabled:
            self._draw_grid()
        
        # Sort components by z-index for proper layering
        sorted_components = sorted(self.components.items(), 
                                 key=lambda x: x[1].z_index)
        
        # Draw components
        for comp_id, comp in sorted_components:
            self._draw_component(comp_id, comp)
        
        # Highlight selected components
        selected_comps = []
        if isinstance(self.selected_component, list):
            selected_comps = self.selected_component
        elif self.selected_component:
            selected_comps = [self.selected_component]
        
        for comp_id in selected_comps:
            if comp_id in self.components:
                comp = self.components[comp_id]
                self.canvas.create_rectangle(
                    comp.x-2, comp.y-2, comp.x+comp.width+2, comp.y+comp.height+2,
                    outline="#ff4757", width=2, tags="selection", dash=(5, 5))
                
                # Show resize handles for single selection
                if len(selected_comps) == 1:
                    self._draw_resize_handles(comp)

        # Calculate and display render time
        render_time = (datetime.now() - start_time).total_seconds() * 1000
        self.render_time = render_time
        self.component_count = len(self.components)
        
        # Update status bar
        self.render_time_label.config(text=f"Render: {render_time:.1f}ms")
        self.component_count_label.config(text=f"Components: {self.component_count}")
        
    def _draw_grid(self):
        """Draw grid lines on canvas"""
        spacing = self.grid_size * self.zoom_level
        
        # Vertical lines
        for x in range(0, self.canvas_width, int(spacing)):
            self.canvas.create_line(x, 0, x, self.canvas_height, 
                                   fill="#e0e0e0", tags="grid")
        
        # Horizontal lines
        for y in range(0, self.canvas_height, int(spacing)):
            self.canvas.create_line(0, y, self.canvas_width, y, 
                                  fill="#e0e0e0", tags="grid")
    
    def _draw_component(self, comp_id, comp):
        """Draw a component on canvas with enhanced styling"""
        x, y = comp.x, comp.y
        width, height = comp.width, comp.height
        
        # Common styling
        fill = comp.styles.get("background", "white")
        outline = comp.styles.get("border-color", "#e1e5e9")
        border_width = int(comp.styles.get("border-width", "1").replace("px", ""))
        
        # Draw component based on type
        if comp.type == "button":
            text = comp.properties.get("text", "Button")
            radius = int(comp.styles.get("border-radius", "6").replace("px", ""))
            self.canvas.create_round_rect(x, y, x+width, y+height, radius=radius,
                                        fill=fill, outline=outline, width=border_width)
            self.canvas.create_text(x+width/2, y+height/2, text=text, 
                                   fill=comp.styles.get("color", "black"))
            
        elif comp.type == "text":
            text = comp.properties.get("content", "Text")
            font = comp.styles.get("font-family", "Arial")
            size = int(comp.styles.get("font-size", "16").replace("px", ""))
            weight = "bold" if "bold" in comp.styles.get("font-weight", "") else "normal"
            self.canvas.create_text(x, y, text=text, anchor="nw", width=width,
                                  font=(font, size, weight), 
                                  fill=comp.styles.get("color", "black"))
            
        elif comp.type == "input":
            text = comp.properties.get("placeholder", "")
            radius = int(comp.styles.get("border-radius", "6").replace("px", ""))
            self.canvas.create_round_rect(x, y, x+width, y+height, radius=radius,
                                        fill=fill, outline=outline, width=border_width)
            self.canvas.create_text(x+10, y+height/2, text=text, anchor="w",
                                  fill="#999999", font=("Arial", 12))
            
        elif comp.type == "image":
            self.canvas.create_rectangle(x, y, x+width, y+height,
                                       fill="#f0f0f0", outline=outline, width=border_width)
            self.canvas.create_text(x+width/2, y+height/2, text="[Image]",
                                  fill="#999999", font=("Arial", 12))
            
        elif comp.type == "card":
            radius = int(comp.styles.get("border-radius", "12").replace("px", ""))
            self.canvas.create_round_rect(x, y, x+width, y+height, radius=radius,
                                        fill=fill, outline=outline, width=border_width)
            
            # Card title
            title = comp.properties.get("title", "Card Title")
            self.canvas.create_text(x+15, y+15, text=title, anchor="nw",
                                  font=("Arial", 14, "bold"), fill="#333333")
            
            # Card content
            content = comp.properties.get("content", "Card content goes here...")
            self.canvas.create_text(x+15, y+45, text=content, anchor="nw", width=width-30,
                                  font=("Arial", 12), fill="#666666")
            
        elif comp.type == "container":
            self.canvas.create_rectangle(x, y, x+width, y+height,
                                       fill="white", outline="#cbd5e0", 
                                       width=2, dash=(5, 5))
            self.canvas.create_text(x+width/2, y+height/2, text="Container",
                                  fill="#999999", font=("Arial", 12))
            
        else:  # Default rectangle for other components
            self.canvas.create_rectangle(x, y, x+width, y+height,
                                       fill=fill, outline=outline, width=border_width)
            self.canvas.create_text(x+width/2, y+height/2, text=comp.type.title(),
                                  fill=comp.styles.get("color", "black"), font=("Arial", 12))
    
    def _draw_resize_handles(self, comp):
        """Draw resize handles for selected component"""
        handle_size = 8
        points = [
            (comp.x, comp.y),  # NW
            (comp.x + comp.width//2, comp.y),  # N
            (comp.x + comp.width, comp.y),  # NE
            (comp.x + comp.width, comp.y + comp.height//2),  # E
            (comp.x + comp.width, comp.y + comp.height),  # SE
            (comp.x + comp.width//2, comp.y + comp.height),  # S
            (comp.x, comp.y + comp.height),  # SW
            (comp.x, comp.y + comp.height//2)  # W
        ]
        
        for i, (x, y) in enumerate(points):
            self.canvas.create_rectangle(
                x-handle_size//2, y-handle_size//2,
                x+handle_size//2, y+handle_size//2,
                fill="#ff4757", outline="#ff4757", tags=f"handle_{i}")
    
    def resize_start(self, event, handle_index):
        """Start resizing a component"""
        if not self.selected_component:
            return
            
        comp = self.components[self.selected_component]
        
        # Store initial positions and sizes
        self.resize_start_x = event.x
        self.resize_start_y = event.y
        self.original_x = comp.x
        self.original_y = comp.y
        self.original_width = comp.width
        self.original_height = comp.height
        self.active_handle = handle_index
        
        # Update status
        self.update_status("Resizing component")

    def resize_drag(self, event):
        """Handle resizing during mouse drag"""
        if not self.selected_component or self.active_handle is None:
            return
            
        comp = self.components[self.selected_component]
        dx = event.x - self.resize_start_x
        dy = event.y - self.resize_start_y
        
        # Handle resizing based on which handle is being dragged
        if self.active_handle == 0:  # top-left
            comp.x = min(self.original_x + dx, self.original_x + self.original_width - 20)
            comp.y = min(self.original_y + dy, self.original_y + self.original_height - 20)
            comp.width = max(20, self.original_width - dx)
            comp.height = max(20, self.original_height - dy)
        elif self.active_handle == 1:  # top-center
            comp.y = min(self.original_y + dy, self.original_y + self.original_height - 20)
            comp.height = max(20, self.original_height - dy)
        elif self.active_handle == 2:  # top-right
            comp.y = min(self.original_y + dy, self.original_y + self.original_height - 20)
            comp.width = max(20, self.original_width + dx)
            comp.height = max(20, self.original_height - dy)
        elif self.active_handle == 3:  # right-center
            comp.width = max(20, self.original_width + dx)
        elif self.active_handle == 4:  # bottom-right
            comp.width = max(20, self.original_width + dx)
            comp.height = max(20, self.original_height + dy)
        elif self.active_handle == 5:  # bottom-center
            comp.height = max(20, self.original_height + dy)
        elif self.active_handle == 6:  # bottom-left
            comp.x = min(self.original_x + dx, self.original_x + self.original_width - 20)
            comp.width = max(20, self.original_width - dx)
            comp.height = max(20, self.original_height + dy)
        elif self.active_handle == 7:  # left-center
            comp.x = min(self.original_x + dx, self.original_x + self.original_width - 20)
            comp.width = max(20, self.original_width - dx)
        
        # Snap to grid if enabled
        if self.snap_to_grid:
            comp.x = round(comp.x / self.grid_size) * self.grid_size
            comp.y = round(comp.y / self.grid_size) * self.grid_size
            comp.width = round(comp.width / self.grid_size) * self.grid_size
            comp.height = round(comp.height / self.grid_size) * self.grid_size
        
        self.render_canvas()

    def resize_end(self):
        """Finish resizing and save state"""
        if self.active_handle is not None:
            self.save_state("Resized component")
            self.active_handle = None

    # Component manipulation methods
    def delete_selected_component(self):
        """Delete the currently selected component(s)"""
        if not self.selected_component:
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        deleted_names = []
        for comp_id in selected_comps:
            if comp_id in self.components:
                deleted_names.append(self.components[comp_id].type)
                del self.components[comp_id]
        
        if deleted_names:
            self.save_state(f"Deleted {', '.join(deleted_names)}")
            self.selected_component = None
            self.render_canvas()
            self.update_properties_panel()
            self.update_layers_panel()
            self.update_status(f"Deleted {len(deleted_names)} component(s)")
    
    def copy_component(self):
        """Copy selected component to clipboard"""
        if not self.selected_component:
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        self.clipboard = []
        for comp_id in selected_comps:
            if comp_id in self.components:
                self.clipboard.append(asdict(self.components[comp_id]))
        
        if self.clipboard:
            self.update_status(f"Copied {len(self.clipboard)} component(s)")
    
    def paste_component(self):
        """Paste component from clipboard"""
        if not hasattr(self, 'clipboard') or not self.clipboard:
            return
            
        self.save_state("Pasted component(s)")
        
        new_selection = []
        for comp_data in self.clipboard:
            # Create new ID and offset position
            new_id = str(uuid.uuid4())
            comp_data['id'] = new_id
            comp_data['x'] += 20
            comp_data['y'] += 20
            
            # Create new component
            component = UIComponent(**comp_data)
            self.components[new_id] = component
            new_selection.append(new_id)
        
        self.selected_component = new_selection[0] if len(new_selection) == 1 else new_selection
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status(f"Pasted {len(new_selection)} component(s)")
    
    def duplicate_component(self):
        """Duplicate selected component(s)"""
        if not self.selected_component:
            return
            
        self.copy_component()
        self.paste_component()
    
    def move_layer_up(self):
        """Move selected component up in z-index"""
        if not self.selected_component:
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        max_z = max(comp.z_index for comp in self.components.values())
        for comp_id in selected_comps:
            if comp_id in self.components and self.components[comp_id].z_index < max_z:
                self.components[comp_id].z_index += 1
        
        self.save_state("Moved layer up")
        self.render_canvas()
        self.update_layers_panel()
    
    def move_layer_down(self):
        """Move selected component down in z-index"""
        if not self.selected_component:
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        min_z = min(comp.z_index for comp in self.components.values())
        for comp_id in selected_comps:
            if comp_id in self.components and self.components[comp_id].z_index > min_z:
                self.components[comp_id].z_index -= 1
        
        self.save_state("Moved layer down")
        self.render_canvas()
        self.update_layers_panel()
    
    def toggle_layer_visibility(self):
        """Toggle visibility of selected component (not fully implemented)"""
        if not self.selected_component:
            return
            
        self.update_status("Visibility toggle not fully implemented")
    
    def toggle_layer_lock(self):
        """Toggle lock state of selected component (not fully implemented)"""
        if not self.selected_component:
            return
            
        self.update_status("Lock toggle not fully implemented")
    
    # Project management methods
    def new_project(self):
        """Create a new project"""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Create new project anyway?"):
                return
                
        self.components = {}
        self.selected_component = None
        self.undo_stack = []
        self.redo_stack = []
        self.project_file = None
        self.is_modified = False
        
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status("New project created")
    
    def open_project(self):
        """Open a project file"""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Open project anyway?"):
                return
                
        file_path = filedialog.askopenfilename(
            filetypes=[("NoirUI Project", "*.nui"), ("All Files", "*.*")])
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            self.components = {}
            for comp_id, comp_data in data['components'].items():
                self.components[comp_id] = UIComponent(**comp_data)
                
            self.project_file = file_path
            self.is_modified = False
            self.undo_stack = []
            self.redo_stack = []
            
            self.render_canvas()
            self.update_properties_panel()
            self.update_layers_panel()
            self.update_status(f"Opened project: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open project: {str(e)}")
    
    def save_project(self):
        """Save current project"""
        if not self.project_file:
            self.save_project_as()
            return
            
        try:
            data = {
                'components': {comp_id: asdict(comp) 
                             for comp_id, comp in self.components.items()},
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.project_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.is_modified = False
            self.update_status(f"Project saved: {os.path.basename(self.project_file)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
    
    def save_project_as(self):
        """Save current project with new filename"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".nui",
            filetypes=[("NoirUI Project", "*.nui"), ("All Files", "*.*")])
        
        if not file_path:
            return
            
        self.project_file = file_path
        self.save_project()
    
    def import_template(self):
        """Import a template file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("NoirUI Template", "*.nut"), ("All Files", "*.*")])
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                template = json.load(f)
                
            self._load_template(template)
            self.update_status(f"Imported template: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import template: {str(e)}")
    
    def export_html(self):
        """Export current design as HTML"""
        if not self.components:
            messagebox.showwarning("Empty Project", "No components to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML File", "*.html"), ("All Files", "*.*")])
        
        if not file_path:
            return
            
        try:
            html = self._generate_html()
            with open(file_path, 'w') as f:
                f.write(html)
                
            self.update_status(f"Exported HTML: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export HTML: {str(e)}")
    
    def export_react(self):
        """Export current design as React components"""
        if not self.components:
            messagebox.showwarning("Empty Project", "No components to export")
            return
            
        folder_path = filedialog.askdirectory()
        
        if not folder_path:
            return
            
        try:
            # Create components folder
            comp_folder = os.path.join(folder_path, "components")
            os.makedirs(comp_folder, exist_ok=True)
            
            # Generate React components
            for comp_id, comp in self.components.items():
                comp_name = f"Component{comp_id[:4]}"
                jsx = self._generate_react_component(comp)
                
                with open(os.path.join(comp_folder, f"{comp_name}.jsx"), 'w') as f:
                    f.write(jsx)
            
            # Generate main App.js
            app_js = self._generate_react_app()
            with open(os.path.join(folder_path, "App.js"), 'w') as f:
                f.write(app_js)
                
            self.update_status(f"Exported React project to: {os.path.basename(folder_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export React: {str(e)}")
    
    # Code generation methods
    def _generate_html(self):
        """Generate HTML for current design"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NoirUI Design</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            position: relative;
            width: 100%;
            height: 100%;
        }
"""
        # Add component styles
        for comp_id, comp in self.components.items():
            html += f"""
        #comp-{comp_id} {{
            position: absolute;
            left: {comp.x}px;
            top: {comp.y}px;
            width: {comp.width}px;
            height: {comp.height}px;
"""
            for prop, value in comp.styles.items():
                html += f"            {prop}: {value};\n"
            html += "        }\n"
        
        html += """
    </style>
</head>
<body>
    <div class="container">
"""
        # Add component HTML
        for comp_id, comp in self.components.items():
            if comp.type == "button":
                html += f'        <button id="comp-{comp_id}">{comp.properties.get("text", "Button")}</button>\n'
            elif comp.type == "text":
                html += f'        <{comp.properties.get("tag", "p")} id="comp-{comp_id}">{comp.properties.get("content", "")}</{comp.properties.get("tag", "p")}>\n'
            elif comp.type == "header":
                level = comp.properties.get("level", "h1")
                html += f'        <{level} id="comp-{comp_id}">{comp.properties.get("content", "")}</{level}>\n'
            elif comp.type == "input":
                html += f'        <input id="comp-{comp_id}" type="{comp.properties.get("type", "text")}" placeholder="{comp.properties.get("placeholder", "")}">\n'
            elif comp.type == "image":
                html += f'        <img id="comp-{comp_id}" src="{comp.properties.get("src", "")}" alt="{comp.properties.get("alt", "")}">\n'
            else:
                html += f'        <div id="comp-{comp_id}">{comp.type.title()}</div>\n'
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def _generate_react_component(self, component):
        """Generate React component code for a single component"""
        comp_name = f"Component{component.id[:4]}"
        
        # Convert styles to React format
        styles = {}
        for prop, value in component.styles.items():
            # Convert CSS property names to React format (camelCase)
            react_prop = prop.replace("-", " ").title().replace(" ", "")
            react_prop = react_prop[0].lower() + react_prop[1:]
            styles[react_prop] = value
        
        style_str = "{\n"
        for prop, value in styles.items():
            style_str += f"        {prop}: '{value}',\n"
        style_str += "    }"
        
        # Generate component JSX
        if component.type == "button":
            return f"""import React from 'react';

const {comp_name} = () => {{
    return (
        <button 
            style={style_str}
        >
            {component.properties.get("text", "Button")}
        </button>
    );
}};

export default {comp_name};
"""
        elif component.type == "text":
            return f"""import React from 'react';

const {comp_name} = () => {{
    return (
        <{component.properties.get("tag", "p")} 
            style={style_str}
        >
            {component.properties.get("content", "")}
        </{component.properties.get("tag", "p")}>
    );
}};

export default {comp_name};
"""
        else:
            return f"""import React from 'react';

const {comp_name} = () => {{
    return (
        <div 
            style={style_str}
        >
            {component.type.title()}
        </div>
    );
}};

export default {comp_name};
"""
    def _generate_react_app(self):
        """Generate main React App component"""
        imports = []
        components = []
        positions = []
        
        for comp_id, comp in self.components.items():
            comp_name = f"Component{comp_id[:4]}"
            imports.append(f"import {comp_name} from './components/{comp_name}';")
            
            components.append(f"            <{comp_name} />")
            positions.append(f"            .{comp_name.replace('Component', 'comp')} {{\n                position: absolute;\n                left: {comp.x}px;\n                top: {comp.y}px;\n                width: {comp.width}px;\n                height: {comp.height}px;\n            }}")
        
        # Precompute the strings to avoid backslashes in f-string
        imports_str = '\n'.join(imports)
        components_str = '\n'.join(components)
        positions_str = '\n'.join(positions)
        
        return f"""import React from 'react';
    {imports_str}

    function App() {{
        return (
            <div className="app">
    {components_str}
            </div>
        );
    }}

    export default App;

    <style>
        .app {{
            position: relative;
            width: 100%;
            height: 100vh;
        }}
        
    {positions_str}
    </style>
    """
    # View and layout methods
    def change_view(self, view):
        """Change view between desktop, tablet, mobile"""
        self.current_view = view
        
        if view == "desktop":
            self.canvas_width, self.canvas_height = 800, 600
        elif view == "tablet":
            self.canvas_width, self.canvas_height = 600, 800
        else:  # mobile
            self.canvas_width, self.canvas_height = 375, 667
        
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self.canvas_info_label.config(text=f"Canvas: {self.canvas_width}x{self.canvas_height}")
        self.render_canvas()
        self.update_status(f"Switched to {view} view")
    
    def zoom_canvas(self, factor, reset=False):
        """Zoom canvas in/out"""
        if reset:
            self.zoom_level = 1.0
        else:
            self.zoom_level *= factor
            self.zoom_level = max(0.1, min(3.0, self.zoom_level))
        
        self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
        self.render_canvas()
    
    def fit_canvas_to_window(self):
        """Fit canvas to current window size"""
        # This is a simplified implementation
        self.zoom_level = 0.8
        self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
        self.render_canvas()
    
    def reset_canvas_zoom(self):
        """Reset canvas zoom to 100%"""
        self.zoom_canvas(1.0, reset=True)
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.grid_enabled = not self.grid_enabled
        self.grid_var.set(self.grid_enabled)
        self.render_canvas()
    
    def toggle_snap(self):
        """Toggle snap to grid"""
        self.snap_to_grid = not self.snap_to_grid
        self.snap_var.set(self.snap_to_grid)
    
    # Property and layer management
    def update_properties_panel(self):
        """Update properties panel for selected component"""
        # Clear existing properties
        for widget in self.props_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_component:
            ttk.Label(self.props_scrollable_frame, text="No component selected").pack(pady=10)
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        if len(selected_comps) > 1:
            ttk.Label(self.props_scrollable_frame, 
                     text=f"{len(selected_comps)} components selected").pack(pady=10)
            return
            
        comp_id = selected_comps[0]
        if comp_id not in self.components:
            return
            
        comp = self.components[comp_id]
        
        # Component info
        info_frame = ttk.LabelFrame(self.props_scrollable_frame, text="Component Info")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text=f"Type: {comp.type}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Position: {comp.x}, {comp.y}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Size: {comp.width}x{comp.height}").pack(anchor="w")
        
        # Position and size controls
        pos_frame = ttk.LabelFrame(self.props_scrollable_frame, text="Position & Size")
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pos_frame, text="X:").grid(row=0, column=0, padx=2, pady=2)
        x_entry = ttk.Entry(pos_frame, width=8)
        x_entry.insert(0, str(comp.x))
        x_entry.grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Label(pos_frame, text="Y:").grid(row=0, column=2, padx=2, pady=2)
        y_entry = ttk.Entry(pos_frame, width=8)
        y_entry.insert(0, str(comp.y))
        y_entry.grid(row=0, column=3, padx=2, pady=2)
        
        ttk.Label(pos_frame, text="Width:").grid(row=1, column=0, padx=2, pady=2)
        w_entry = ttk.Entry(pos_frame, width=8)
        w_entry.insert(0, str(comp.width))
        w_entry.grid(row=1, column=1, padx=2, pady=2)
        
        ttk.Label(pos_frame, text="Height:").grid(row=1, column=2, padx=2, pady=2)
        h_entry = ttk.Entry(pos_frame, width=8)
        h_entry.insert(0, str(comp.height))
        h_entry.grid(row=1, column=3, padx=2, pady=2)
        
        def update_position():
            try:
                comp.x = int(x_entry.get())
                comp.y = int(y_entry.get())
                comp.width = int(w_entry.get())
                comp.height = int(h_entry.get())
                self.render_canvas()
            except ValueError:
                pass
                
        update_btn = ttk.Button(pos_frame, text="Update", command=update_position)
        update_btn.grid(row=2, column=0, columnspan=4, pady=5)
        
        # Properties editor
        props_frame = ttk.LabelFrame(self.props_scrollable_frame, text="Properties")
        props_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for prop, value in comp.properties.items():
            row_frame = ttk.Frame(props_frame)
            row_frame.pack(fill=tk.X, padx=2, pady=2)
            
            ttk.Label(row_frame, text=f"{prop}:").pack(side=tk.LEFT)
            entry = ttk.Entry(row_frame)
            entry.insert(0, str(value))
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            def make_update_func(p, e=entry):
                def update_prop():
                    comp.properties[p] = e.get()
                    self.render_canvas()
                return update_prop
                
            entry.bind("<FocusOut>", lambda e, p=prop: make_update_func(p)())
        
        # Styles editor
        styles_frame = ttk.LabelFrame(self.props_scrollable_frame, text="Styles")
        styles_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for style, value in comp.styles.items():
            row_frame = ttk.Frame(styles_frame)
            row_frame.pack(fill=tk.X, padx=2, pady=2)
            
            ttk.Label(row_frame, text=f"{style}:").pack(side=tk.LEFT)
            entry = ttk.Entry(row_frame)
            entry.insert(0, str(value))
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            def make_update_func(s, e=entry):
                def update_style():
                    comp.styles[s] = e.get()
                    self.render_canvas()
                return update_style
                
            entry.bind("<FocusOut>", lambda e, s=style: make_update_func(s)())
    
    def update_layers_panel(self):
        """Update layers panel with current component hierarchy"""
        self.layers_tree.delete(*self.layers_tree.get_children())
        
        # Sort components by z-index
        sorted_components = sorted(self.components.items(), 
                                 key=lambda x: x[1].z_index)
        
        for comp_id, comp in sorted_components:
            self.layers_tree.insert("", "end", comp_id, text=f"{comp.type} ({comp_id[:4]})")
    
    def _on_layer_select(self, event):
        """Handle layer selection from layers panel"""
        item = self.layers_tree.focus()
        if item in self.components:
            self.selected_component = item
            self.render_canvas()
            self.update_properties_panel()
    
    # Undo/Redo functionality
    def save_state(self, description=""):
        """Save current state to undo stack"""
        state = ProjectState(
            components={k: asdict(v) for k, v in self.components.items()},
            timestamp=datetime.now().isoformat(),
            description=description
        )
        
        self.undo_stack.append(state)
        self.redo_stack = []  # Clear redo stack
        self.is_modified = True
        
        # Update history panel
        self.history_listbox.insert(0, f"{state.timestamp[:19]} - {state.description}")
    
    def undo(self):
        """Undo last action"""
        if not self.undo_stack:
            return
            
        # Save current state to redo stack
        current_state = ProjectState(
            components={k: asdict(v) for k, v in self.components.items()},
            timestamp=datetime.now().isoformat(),
            description="Before undo"
        )
        self.redo_stack.append(current_state)
        
        # Restore previous state
        state = self.undo_stack.pop()
        self.components = {}
        for comp_id, comp_data in state.components.items():
            self.components[comp_id] = UIComponent(**comp_data)
        
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status(f"Undo: {state.description}")
        
        # Update history panel
        self.history_listbox.delete(0)
    
    def redo(self):
        """Redo last undone action"""
        if not self.redo_stack:
            return
            
        # Save current state to undo stack
        current_state = ProjectState(
            components={k: asdict(v) for k, v in self.components.items()},
            timestamp=datetime.now().isoformat(),
            description="Before redo"
        )
        self.undo_stack.append(current_state)
        
        # Restore next state
        state = self.redo_stack.pop()
        self.components = {}
        for comp_id, comp_data in state.components.items():
            self.components[comp_id] = UIComponent(**comp_data)
        
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status(f"Redo: {state.description}")
        
        # Update history panel
        self.history_listbox.insert(0, f"{state.timestamp[:19]} - {state.description}")
    
    def revert_to_history(self):
        """Revert to selected history state"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        
        # Save current state to redo stack
        current_state = ProjectState(
            components={k: asdict(v) for k, v in self.components.items()},
            timestamp=datetime.now().isoformat(),
            description="Before revert"
        )
        self.redo_stack.append(current_state)
        
        # Get the state to revert to
        state = self.undo_stack[index]
        
        # Apply the state
        self.components = {}
        for comp_id, comp_data in state.components.items():
            self.components[comp_id] = UIComponent(**comp_data)
        
        # Truncate undo stack
        self.undo_stack = self.undo_stack[:index]
        
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status(f"Reverted to: {state.description}")
        
        # Update history panel
        for i in range(index, self.history_listbox.size()):
            self.history_listbox.delete(index)
    
    def clear_history(self):
        """Clear undo history"""
        if not messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            return
            
        self.undo_stack = []
        self.redo_stack = []
        self.history_listbox.delete(0, tk.END)
        self.update_status("History cleared")
    
    # Template methods
    def _load_selected_template(self):
        """Load the selected template"""
        selection = self.template_listbox.curselection()
        if not selection:
            return
            
        template_name = list(self.templates.keys())[selection[0]]
        template = self.templates[template_name]
        self._load_template(template)
        self.update_status(f"Loaded template: {template['name']}")
    
    def _load_template(self, template):
        """Load components from template"""
        if not template or 'components' not in template:
            return
            
        self.save_state(f"Loaded template: {template.get('name', '')}")
        self.components = {}
        
        for comp_data in template['components']:
            comp_id = str(uuid.uuid4())
            component = UIComponent(
                id=comp_id,
                type=comp_data['type'],
                x=comp_data['x'],
                y=comp_data['y'],
                width=comp_data['width'],
                height=comp_data['height'],
                properties=comp_data.get('properties', {}),
                styles=comp_data.get('styles', {}),
                z_index=len(self.components)
            )
            self.components[comp_id] = component
        
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
    
    def save_as_template(self):
        """Save current design as a template"""
        if not self.components:
            messagebox.showwarning("Empty Design", "No components to save as template")
            return
            
        template_name = simpledialog.askstring("Save Template", "Enter template name:")
        if not template_name:
            return
            
        template = {
            "name": template_name,
            "description": "Saved from NoirUI",
            "components": [asdict(comp) for comp in self.components.values()]
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".nut",
            filetypes=[("NoirUI Template", "*.nut"), ("All Files", "*.*")],
            initialfile=f"{template_name.lower().replace(' ', '_')}.nut")
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            self.update_status(f"Saved template: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {str(e)}")
    
    # AI and helper methods
    def ai_suggest_layout(self):
        """Generate AI suggestions for layout improvements"""
        if not self.components:
            messagebox.showinfo("Empty Canvas", "Add some components first to get suggestions")
            return
            
        # Mock AI suggestions
        suggestions = [
            "Consider adding more spacing between components for better readability",
            "The color scheme could be more consistent - try using a primary color palette",
            "Align the left edges of these components for a cleaner look",
            "The text contrast could be improved for better accessibility",
            "Consider grouping related components in containers"
        ]
        
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "AI Suggestions:\n\n")
        self.ai_text.insert(tk.END, "\n".join(f"• {s}" for s in suggestions))
        
        self.left_notebook.select(self.ai_tab)
        self.update_status("Generated AI layout suggestions")
    
    def ai_optimize_colors(self):
        """Generate AI suggestions for color optimization"""
        if not self.components:
            return
            
        # Mock color suggestions
        palette = self.color_palettes.get("modern_blue", {})
        suggestions = [
            f"Primary color: {palette.get('primary', '#3b82f6')}",
            f"Secondary color: {palette.get('secondary', '#64748b')}",
            f"Accent color: {palette.get('info', '#06b6d4')}",
            "Text colors should have sufficient contrast (4.5:1 ratio)"
        ]
        
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "Color Optimization:\n\n")
        self.ai_text.insert(tk.END, "\n".join(f"• {s}" for s in suggestions))
        
        self.left_notebook.select(self.ai_tab)
        self.update_status("Generated AI color suggestions")
    
    def ai_improve_accessibility(self):
        """Generate AI suggestions for accessibility improvements"""
        if not self.components:
            return
            
        # Mock accessibility suggestions
        suggestions = [
            "Increase text contrast for better readability",
            "Add alt text to all images",
            "Ensure interactive elements have sufficient size (min 44x44px)",
            "Provide text alternatives for non-text content",
            "Use semantic HTML elements where possible"
        ]
        
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "Accessibility Improvements:\n\n")
        self.ai_text.insert(tk.END, "\n".join(f"• {s}" for s in suggestions))
        
        self.left_notebook.select(self.ai_tab)
        self.update_status("Generated AI accessibility suggestions")
    
    def show_ai_assistant(self):
        """Show AI assistant panel"""
        self.left_notebook.select(self.ai_tab)
    
    def check_accessibility(self):
        """Run accessibility checks on current design"""
        issues = []
        
        for comp_id, comp in self.components.items():
            if comp.type == "image" and not comp.properties.get("alt", ""):
                issues.append(f"Image component {comp_id[:4]} missing alt text")
            
            if comp.type in ["text", "header"]:
                color = comp.styles.get("color", "#000000")
                bg_color = comp.styles.get("background", "#ffffff")
                # Simple contrast check (would need proper algorithm for real implementation)
                if color.lower() == bg_color.lower():
                    issues.append(f"Text component {comp_id[:4]} has poor contrast")
        
        self.acc_text.delete(1.0, tk.END)
        
        if issues:
            self.acc_text.insert(tk.END, "Accessibility Issues Found:\n\n")
            self.acc_text.insert(tk.END, "\n".join(f"• {issue}" for issue in issues))
            self.right_notebook.select(self.inspector_tab)
            self.update_status(f"Found {len(issues)} accessibility issues")
        else:
            self.acc_text.insert(tk.END, "No accessibility issues found!")
            self.update_status("No accessibility issues found")
    
    def performance_audit(self):
        """Run performance audit on current design"""
        # Mock performance metrics
        component_count = len(self.components)
        render_time = self.render_time
        complexity = "Low"
        
        if component_count > 20:
            complexity = "High"
        elif component_count > 10:
            complexity = "Medium"
        
        suggestions = [
            f"Component count: {component_count} ({complexity} complexity)",
            f"Render time: {render_time:.1f}ms",
            "Consider reducing nested containers for better performance",
            "Optimize image assets for faster loading",
            "Minimize use of complex shadows and gradients"
        ]
        
        self.perf_text.delete(1.0, tk.END)
        self.perf_text.insert(tk.END, "Performance Audit Results:\n\n")
        self.perf_text.insert(tk.END, "\n".join(f"• {s}" for s in suggestions))
        
        self.right_notebook.select(self.inspector_tab)
        self.update_status("Ran performance audit")
    
    def auto_align_components(self):
        """Automatically align selected components"""
        if not self.selected_component or isinstance(self.selected_component, list) and len(self.selected_component) < 2:
            messagebox.showinfo("Alignment", "Select multiple components to align")
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        # Get all selected components
        components = [self.components[comp_id] for comp_id in selected_comps if comp_id in self.components]
        if len(components) < 2:
            return
            
        # Ask for alignment type
        align_type = simpledialog.askstring("Alignment", "Align by: (left, right, top, bottom, center, distribute)", 
                                           parent=self.root)
        if not align_type:
            return
            
        align_type = align_type.lower()
        
        if align_type == "left":
            min_x = min(comp.x for comp in components)
            for comp in components:
                comp.x = min_x
        elif align_type == "right":
            max_x = max(comp.x + comp.width for comp in components)
            for comp in components:
                comp.x = max_x - comp.width
        elif align_type == "top":
            min_y = min(comp.y for comp in components)
            for comp in components:
                comp.y = min_y
        elif align_type == "bottom":
            max_y = max(comp.y + comp.height for comp in components)
            for comp in components:
                comp.y = max_y - comp.height
        elif align_type == "center":
            avg_x = sum(comp.x + comp.width/2 for comp in components) / len(components)
            for comp in components:
                comp.x = avg_x - comp.width/2
        elif align_type == "distribute":
            # Distribute horizontally
            min_x = min(comp.x for comp in components)
            max_x = max(comp.x + comp.width for comp in components)
            total_width = max_x - min_x
            spacing = (total_width - sum(comp.width for comp in components)) / (len(components) - 1)
            
            x = min_x
            for comp in sorted(components, key=lambda c: c.x):
                comp.x = x
                x += comp.width + spacing
        
        self.save_state("Auto-aligned components")
        self.render_canvas()
        self.update_status(f"Aligned components: {align_type}")
    
    def group_components(self):
        """Group selected components into a container"""
        if not self.selected_component or isinstance(self.selected_component, list) and len(self.selected_component) < 2:
            messagebox.showinfo("Group", "Select multiple components to group")
            return
            
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        components = [self.components[comp_id] for comp_id in selected_comps if comp_id in self.components]
        
        if len(components) < 2:
            return
            
        # Calculate bounds for new container
        min_x = min(comp.x for comp in components)
        min_y = min(comp.y for comp in components)
        max_x = max(comp.x + comp.width for comp in components)
        max_y = max(comp.y + comp.height for comp in components)
        
        # Create container
        container = UIComponent(
            id=str(uuid.uuid4()),
            type="container",
            x=min_x - 10,
            y=min_y - 10,
            width=(max_x - min_x) + 20,
            height=(max_y - min_y) + 20,
            properties={"flex_direction": "column"},
            styles={"background": "#f8f9fa", "padding": "10px"},
            z_index=max(comp.z_index for comp in components) + 1
        )
        
        # Add components as children
        container.children = [comp.id for comp in components]
        
        # Adjust component positions relative to container
        for comp in components:
            comp.x -= container.x
            comp.y -= container.y
            comp.z_index += 1  # Ensure children are above container
        
        self.components[container.id] = container
        self.selected_component = container.id
        
        self.save_state("Grouped components")
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status("Grouped components into container")
    
    def select_all(self):
        """Select all components"""
        if not self.components:
            return
            
        self.selected_component = list(self.components.keys())
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status("Selected all components")
    
    def deselect_all(self):
        """Deselect all components"""
        self.selected_component = None
        self.render_canvas()
        self.update_properties_panel()
        self.update_layers_panel()
        self.update_status("Selection cleared")
    
    def preview_ui(self):
        """Preview UI in web browser"""
        if not self.components:
            messagebox.showwarning("Empty Design", "No components to preview")
            return
            
        html = self._generate_html()
        
        # Create temp file and open in browser
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            f.write(html)
            temp_path = f.name
            
        webbrowser.open(f"file://{temp_path}")
        self.update_status("Opened preview in browser")
    
    def apply_theme(self, palette_name):
        """Apply color theme to selected components"""
        if palette_name not in self.color_palettes:
            return
            
        if not self.selected_component:
            messagebox.showinfo("Theme", "Select components to apply theme")
            return
            
        palette = self.color_palettes[palette_name]
        selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
        
        for comp_id in selected_comps:
            if comp_id in self.components:
                comp = self.components[comp_id]
                
                # Apply theme based on component type
                if comp.type == "button":
                    comp.styles["background"] = palette["primary"]
                    comp.styles["color"] = "white"
                elif comp.type in ["card", "container"]:
                    comp.styles["background"] = palette["light"]
                elif comp.type in ["text", "header"]:
                    comp.styles["color"] = palette["dark"]
        
        self.save_state(f"Applied {palette_name} theme")
        self.render_canvas()
        self.update_properties_panel()
        self.update_status(f"Applied {palette_name} theme to selected components")
    
    def pick_primary_color(self):
        """Pick primary color from color dialog"""
        color = colorchooser.askcolor(title="Pick Primary Color")
        if color[1]:
            if not self.selected_component:
                return
                
            selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
            
            for comp_id in selected_comps:
                if comp_id in self.components:
                    comp = self.components[comp_id]
                    if comp.type == "button":
                        comp.styles["background"] = color[1]
                    elif comp.type in ["text", "header"]:
                        comp.styles["color"] = color[1]
            
            self.save_state("Changed primary color")
            self.render_canvas()
            self.update_properties_panel()
            self.update_status("Updated primary color")
    
    def pick_accent_color(self):
        """Pick accent color from color dialog"""
        color = colorchooser.askcolor(title="Pick Accent Color")
        if color[1]:
            if not self.selected_component:
                return
                
            selected_comps = [self.selected_component] if not isinstance(self.selected_component, list) else self.selected_component
            
            for comp_id in selected_comps:
                if comp_id in self.components:
                    comp = self.components[comp_id]
                    if comp.type in ["card", "container"]:
                        comp.styles["border-color"] = color[1]
                    elif comp.type == "button":
                        comp.styles["border-color"] = color[1]
            
            self.save_state("Changed accent color")
            self.render_canvas()
            self.update_properties_panel()
            self.update_status("Updated accent color")
    
    # UI helper methods
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
    
    def show_component_library(self):
        """Show component library panel"""
        self.left_notebook.select(0)  # First tab is components
    
    def show_style_guide(self):
        """Show style guide panel"""
        self.left_notebook.select(2)  # Third tab is themes
    
    def show_tutorial(self):
        """Show tutorial/documentation"""
        webbrowser.open("https://github.com/your-repo/noirui/docs")
        self.update_status("Opened documentation in browser")
    
    def show_shortcuts(self):
        """Show keyboard shortcuts reference"""
        shortcuts = """
        Keyboard Shortcuts:
        Ctrl+N - New Project
        Ctrl+O - Open Project
        Ctrl+S - Save Project
        Ctrl+Shift+S - Save As
        Ctrl+Z - Undo
        Ctrl+Y - Redo
        Ctrl+C - Copy
        Ctrl+V - Paste
        Del - Delete
        Ctrl+A - Select All
        Ctrl++ - Zoom In
        Ctrl+- - Zoom Out
        Ctrl+0 - Reset Zoom
        F5 - Preview
        Ctrl+D - Duplicate
        Ctrl+G - Group
        Esc - Deselect All
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        NoirUI - Professional Low-Code UI Designer
        Version 1.0.0
        
        A powerful tool for designing modern user interfaces
        with a visual drag-and-drop interface.
        
        © 2023 NoirUI Team
        """
        messagebox.showinfo("About NoirUI", about_text)
    
    # Event handlers
    def _on_component_double_click(self, event):
        """Handle double click on component in library"""
        item = self.comp_tree.focus()
        comp_type = self.comp_tree.item(item, "values")[0]
        if comp_type:
            self.add_component(comp_type)
    
    def _on_template_double_click(self, event):
        """Handle double click on template"""
        self._load_selected_template()
    
    def _on_zoom_change(self, event):
        """Handle zoom level change from combobox"""
        zoom_str = self.zoom_var.get().replace("%", "")
        try:
            zoom = float(zoom_str) / 100
            self.zoom_canvas(zoom, reset=True)
        except ValueError:
            pass
    
    def _on_grid_size_change(self):
        """Handle grid size change"""
        self.grid_size = self.grid_size_var.get()
        if self.grid_enabled:
            self.render_canvas()
    
    def _filter_components(self, event):
        """Filter components based on search text"""
        search_term = self.comp_search_var.get().lower()
        
        for child in self.comp_tree.get_children():
            self.comp_tree.item(child, open=False)
            for subchild in self.comp_tree.get_children(child):
                text = self.comp_tree.item(subchild, "text").lower()
                values = self.comp_tree.item(subchild, "values")
                if search_term in text or (values and search_term in values[0].lower()):
                    self.comp_tree.item(child, open=True)
                    self.comp_tree.see(subchild)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

# Helper function for rounded rectangles
def create_round_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1+radius, y1,
        x1+radius, y1,
        x2-radius, y1,
        x2-radius, y1,
        x2, y1,
        x2, y1+radius,
        x2, y1+radius,
        x2, y2-radius,
        x2, y2-radius,
        x2, y2,
        x2-radius, y2,
        x2-radius, y2,
        x1+radius, y2,
        x1+radius, y2,
        x1, y2,
        x1, y2-radius,
        x1, y2-radius,
        x1, y1+radius,
        x1, y1+radius,
        x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# Monkey patch Canvas to add round_rect method
tk.Canvas.create_round_rect = create_round_rect

if __name__ == "__main__":
    app = NoirUI()
    app.run()