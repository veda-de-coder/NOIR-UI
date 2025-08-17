"""
Main entry point for the NOIR UI application.
"""
from core.service_container import ServiceContainer
from core.event_bus import EventBus
from core.config import Config
from services.project_service import ProjectService
from services.selection_service import SelectionService
from ui.main_window import MainWindow

def main():
    """Initialize and run the application."""
    # Create service container
    container = ServiceContainer()
    
    # Register core services
    container.register(EventBus)
    container.register(Config)
    
    # Register application services
    container.register(ProjectService)
    container.register(SelectionService)
    
    # Create and run main window
    window = MainWindow(container)
    window.run()

if __name__ == "__main__":
    main()
