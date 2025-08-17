"""
Project management service implementation.
"""
from typing import Optional
from pathlib import Path
import json

from core.models import Project, Component
from core.event_bus import EventBus, EventType

class ProjectService:
    """Service for managing projects and their components."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.current_project: Optional[Project] = None
    
    def create_project(self, name: str) -> Project:
        """Create a new project."""
        project = Project(name=name)
        self.current_project = project
        self.event_bus.publish_from(
            EventType.STATE_CHANGED,
            {'project_id': project.id},
            'project_service'
        )
        return project
    
    def load_project(self, path: Path) -> Project:
        """Load a project from file."""
        with open(path, 'r') as f:
            data = json.load(f)
            project = Project.from_dict(data)
            self.current_project = project
            self.event_bus.publish_from(
                EventType.STATE_CHANGED,
                {'project_id': project.id},
                'project_service'
            )
            return project
    
    def save_project(self, path: Path):
        """Save current project to file."""
        if not self.current_project:
            raise ValueError("No project is currently loaded")
        
        with open(path, 'w') as f:
            json.dump(self.current_project.to_dict(), f, indent=4)
    
    def add_component(self, component: Component):
        """Add a component to the current project."""
        if not self.current_project:
            raise ValueError("No project is currently loaded")
        
        self.current_project.components.append(component)
        self.event_bus.publish_from(
            EventType.COMPONENT_CREATED,
            {'component_id': component.id},
            'project_service'
        )
    
    def remove_component(self, component_id: str):
        """Remove a component from the current project."""
        if not self.current_project:
            raise ValueError("No project is currently loaded")
        
        self.current_project.components = [
            c for c in self.current_project.components
            if c.id != component_id
        ]
        self.event_bus.publish_from(
            EventType.COMPONENT_DELETED,
            {'component_id': component_id},
            'project_service'
        )
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by its ID."""
        if not self.current_project:
            return None
        
        for component in self.current_project.components:
            if component.id == component_id:
                return component
        return None
