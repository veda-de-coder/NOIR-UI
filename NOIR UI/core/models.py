"""
Core models and data structures for the application.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from uuid import uuid4

@dataclass
class Component:
    """Base class for all UI components."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = field(default="base")
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List['Component'] = field(default_factory=list)
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation."""
        return {
            'id': self.id,
            'type': self.type,
            'properties': self.properties,
            'children': [child.to_dict() for child in self.children],
            'parent_id': self.parent_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create component from dictionary representation."""
        children = [cls.from_dict(child) for child in data.get('children', [])]
        return cls(
            id=data.get('id', str(uuid4())),
            type=data.get('type', 'base'),
            properties=data.get('properties', {}),
            children=children,
            parent_id=data.get('parent_id')
        )

@dataclass
class Project:
    """Project model containing all UI components and metadata."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    components: List[Component] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _component_index: Dict[str, Component] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Initialize the component index."""
        self._component_index = {}
        for component in self.components:
            self._index_component(component)

    def _index_component(self, component: Component):
        """Add a component and its children to the index."""
        self._component_index[component.id] = component
        for child in component.children:
            self._index_component(child)

        # In Project class
        def add_component(self, component: Component):
            self.components.append(component)
            self._index_component(component)

        def remove_component(self, component_id: str):
            self.components = [c for c in self.components if c.id != component_id]
            # Recursively remove from index
            if component_id in self._component_index:
                comp = self._component_index[component_id]
                for child in comp.children:
                    self.remove_component(child.id)
                del self._component_index[component_id]

    def get_component_by_id(self, component_id: str) -> Optional[Component]:
        """O(1) component lookup by ID."""
        return self._component_index.get(component_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'components': [comp.to_dict() for comp in self.components],
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary representation."""
        components = [Component.from_dict(comp) for comp in data.get('components', [])]
        return cls(
            id=data.get('id', str(uuid4())),
            name=data.get('name', ''),
            components=components,
            metadata=data.get('metadata', {})
        )
