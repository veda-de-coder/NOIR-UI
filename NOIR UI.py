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
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
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