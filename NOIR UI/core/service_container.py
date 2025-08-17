"""
Dependency injection container for managing application services.
"""
from typing import Dict, Type, Any
from core.event_bus import EventBus
from core.config import Config

class ServiceContainer:
    """
    Service container implementing dependency injection pattern.
    Manages application-wide service instances and their dependencies.
    """
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._instances: Dict[Type, Any] = {}
        
        # Register core services
        self.register(EventBus)
        self.register(Config)
    
    def register(self, service_type: Type, instance: Any = None):
        """Register a service type with an optional instance."""
        # If no instance is provided, register the type itself for lazy instantiation
        self._services[service_type] = instance if instance is not None else service_type
    
    def get(self, service_type: Type) -> Any:
        """Get an instance of a registered service."""
        # Return existing instance if available
        if service_type in self._instances:
            return self._instances[service_type]
        
        # Get the service
        service = self._services.get(service_type)
        if service is None:
            return None  # Return None if the service is not registered
        
        # If service is a type, instantiate it
        if isinstance(service, type):
            instance = self._instantiate(service)
            self._instances[service_type] = instance
            return instance
        
        # If service is an instance, store and return it
        self._instances[service_type] = service
        return service
    
    def _instantiate(self, service_type: Type) -> Any:
        """Instantiate a service with its dependencies."""
        # Get service initialization parameters
        params = {}
        try:
            init = service_type.__init__
            if init and hasattr(init, '__annotations__'):
                for param_name, param_type in init.__annotations__.items():
                    if param_name != 'return':  # Skip return annotation
                        dependency = self.get(param_type)
                        if dependency is not None:
                            params[param_name] = dependency
        except AttributeError:
            pass
        return service_type(**params)
    
    def clear(self):
        """Clear all service instances."""
        self._instances.clear()
