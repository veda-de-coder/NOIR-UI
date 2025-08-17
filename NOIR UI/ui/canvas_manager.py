"""
Canvas management and rendering implementation with optimized rendering.
"""
from typing import Optional, Tuple, Dict, Any, Set
from dataclasses import dataclass
import time
from PIL import Image, ImageTk
from core.event_bus import EventBus, EventType
from core.config import Config
from services.selection_service import SelectionService

@dataclass
class DirtyRegion:
    """Represents a region of the canvas that needs redrawing."""
    x1: int
    y1: int
    x2: int
    y2: int

    def expand(self, margin: int = 2):
        """Expand the region by a margin."""
        self.x1 -= margin
        self.y1 -= margin
        self.x2 += margin
        self.y2 += margin

    def intersects(self, other: 'DirtyRegion') -> bool:
        """Check if this region intersects with another."""
        return not (self.x2 < other.x1 or self.x1 > other.x2 or
                   self.y2 < other.y1 or self.y1 > other.y2)

class CanvasManager:
    """Manages the canvas area and rendering with optimization."""
    
    def __init__(
        self,
        event_bus: EventBus,
        config: Config,
        selection_service: SelectionService
    ):
        self.event_bus = event_bus
        self.config = config
        self.selection_service = selection_service
        self.zoom_level: float = 1.0
        self.offset: Tuple[float, float] = (0.0, 0.0)
        
        # Rendering optimization
        self._cache: Dict[str, ImageTk.PhotoImage] = {}
        self._dirty_regions: Set[DirtyRegion] = set()
        self._last_render_time: float = 0
        self._render_throttle: float = 1/60  # 60 FPS max
        self._is_dragging: bool = False
        self._drag_throttle_timer: Optional[str] = None
        
        # Component caching
        self._static_components: Set[str] = set()
        self._component_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers for canvas-related events."""
        self.event_bus.subscribe(
            EventType.SELECTION_CHANGED,
            self._handle_selection_changed
        )
        self.event_bus.subscribe(
            EventType.COMPONENT_CREATED,
            self._handle_component_created
        )
        
    def mark_dirty_region(self, x1: int, y1: int, x2: int, y2: int):
        """Mark a region of the canvas as needing redraw."""
        new_region = DirtyRegion(x1, y1, x2, y2)
        new_region.expand()
        
        # Merge overlapping regions
        overlapping = set()
        for region in self._dirty_regions:
            if region.intersects(new_region):
                overlapping.add(region)
                new_region.x1 = min(new_region.x1, region.x1)
                new_region.y1 = min(new_region.y1, region.y1)
                new_region.x2 = max(new_region.x2, region.x2)
                new_region.y2 = max(new_region.y2, region.y2)
        
        self._dirty_regions -= overlapping
        self._dirty_regions.add(new_region)
    
    def _render_dirty_regions(self):
        """Render only the dirty regions of the canvas."""
        current_time = time.time()
        if current_time - self._last_render_time < self._render_throttle:
            return
        
        for region in self._dirty_regions:
            # Clear region
            self.canvas.delete("region", region.x1, region.y1, region.x2, region.y2)
            
            # Render static components in region
            for comp_id in self._static_components:
                bounds = self._component_bounds.get(comp_id)
                if bounds and self._regions_intersect(region, bounds):
                    self._render_cached_component(comp_id, bounds)
            
            # Render dynamic components in region
            self._render_dynamic_components(region)
        
        self._dirty_regions.clear()
        self._last_render_time = current_time
    
    def _render_cached_component(self, component_id: str, bounds: Tuple[int, int, int, int]):
        """Render a cached component."""
        cache = self._cache.get(component_id)
        if cache:
            self.canvas.create_image(
                bounds[0],
                bounds[1],
                image=cache,
                anchor="nw",
                tags=("component", component_id)
            )
    
    def _cache_component(self, component_id: str, bounds: Tuple[int, int, int, int]):
        """Cache a static component as a bitmap."""
        # Create offscreen image
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Render component to image
        self._render_component_to_image(component_id, image)
        
        # Store in cache
        photo = ImageTk.PhotoImage(image)
        self._cache[component_id] = photo
        self._component_bounds[component_id] = bounds
    
    def _handle_drag_throttled(self, event):
        """Throttled handler for drag events."""
        current_time = time.time()
        if self._is_dragging and current_time - self._last_render_time >= self._render_throttle:
            self._handle_drag(event)
            self._last_render_time = current_time
    
    def zoom_in(self):
        """Increase canvas zoom level."""
        self.zoom_level *= self.config.ui.zoom_factor_in
        self._notify_canvas_updated()
    
    def zoom_out(self):
        """Decrease canvas zoom level."""
        self.zoom_level *= self.config.ui.zoom_factor_out
        self._notify_canvas_updated()
    
    def pan(self, dx: float, dy: float):
        """Pan the canvas by the given delta."""
        self.offset = (
            self.offset[0] + dx,
            self.offset[1] + dy
        )
        self._notify_canvas_updated()
    
    def screen_to_canvas(self, x: float, y: float) -> Tuple[float, float]:
        """Convert screen coordinates to canvas coordinates."""
        return (
            (x - self.offset[0]) / self.zoom_level,
            (y - self.offset[1]) / self.zoom_level
        )
    
    def canvas_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert canvas coordinates to screen coordinates."""
        return (
            x * self.zoom_level + self.offset[0],
            y * self.zoom_level + self.offset[1]
        )
    
    def _handle_selection_changed(self, event):
        """Handle selection change events."""
        self._notify_canvas_updated()
    
    def _handle_component_created(self, event):
        """Handle component creation events."""
        self._notify_canvas_updated()
    
    def _notify_canvas_updated(self):
        """Notify listeners that the canvas has been updated."""
        self.event_bus.publish_from(
            EventType.CANVAS_UPDATED,
            {
                'zoom_level': self.zoom_level,
                'offset': self.offset
            },
            'canvas_manager'
        )
