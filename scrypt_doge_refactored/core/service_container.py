"""
Service Container for dependency injection and service management.
Provides centralized service registration and resolution.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    service_type: Type
    instance: Any = None
    singleton: bool = True
    factory: Optional[Callable] = None
    dependencies: list = None
    initialized: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceContainer:
    """
    Dependency injection container for managing services.
    Supports singleton and transient services with dependency resolution.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._logger = logging.getLogger(__name__)
        self._initialization_order: list = []
    
    def register_singleton(self, name: str, service_type: Type[T], factory: Callable[[], T] = None, dependencies: list = None) -> 'ServiceContainer':
        """Register a singleton service"""
        self._services[name] = ServiceInfo(
            name=name,
            service_type=service_type,
            singleton=True,
            factory=factory,
            dependencies=dependencies or []
        )
        self._logger.debug(f"Registered singleton service: {name}")
        return self
    
    def register_transient(self, name: str, service_type: Type[T], factory: Callable[[], T] = None, dependencies: list = None) -> 'ServiceContainer':
        """Register a transient service (new instance each time)"""
        self._services[name] = ServiceInfo(
            name=name,
            service_type=service_type,
            singleton=False,
            factory=factory,
            dependencies=dependencies or []
        )
        self._logger.debug(f"Registered transient service: {name}")
        return self
    
    def register_instance(self, name: str, instance: T) -> 'ServiceContainer':
        """Register an existing instance as a singleton"""
        self._services[name] = ServiceInfo(
            name=name,
            service_type=type(instance),
            instance=instance,
            singleton=True,
            initialized=True,
            created_at=datetime.now()
        )
        self._logger.debug(f"Registered instance: {name}")
        return self
    
    def resolve(self, name: str) -> Any:
        """Resolve a service by name"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        
        service_info = self._services[name]
        
        # If singleton and already created, return existing instance
        if service_info.singleton and service_info.instance is not None:
            return service_info.instance
        
        # Create new instance
        instance = self._create_instance(service_info)
        
        # Store instance if singleton
        if service_info.singleton:
            service_info.instance = instance
            service_info.initialized = True
            service_info.created_at = datetime.now()
        
        return instance
    
    def resolve_type(self, service_type: Type[T]) -> T:
        """Resolve a service by type"""
        for service_info in self._services.values():
            if service_info.service_type == service_type:
                return self.resolve(service_info.name)
        
        raise ValueError(f"No service registered for type: {service_type}")
    
    def _create_instance(self, service_info: ServiceInfo) -> Any:
        """Create an instance of a service"""
        try:
            # Resolve dependencies first
            resolved_deps = {}
            for dep_name in service_info.dependencies:
                resolved_deps[dep_name] = self.resolve(dep_name)
            
            # Create instance using factory or constructor
            if service_info.factory:
                if service_info.dependencies:
                    instance = service_info.factory(**resolved_deps)
                else:
                    instance = service_info.factory()
            else:
                if service_info.dependencies:
                    # Try to pass dependencies as constructor arguments
                    instance = service_info.service_type(**resolved_deps)
                else:
                    instance = service_info.service_type()
            
            self._logger.debug(f"Created instance of service: {service_info.name}")
            return instance
            
        except Exception as e:
            self._logger.error(f"Failed to create instance of service '{service_info.name}': {e}")
            raise
    
    def is_registered(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services
    
    def get_service_info(self, name: str) -> Optional[ServiceInfo]:
        """Get information about a registered service"""
        return self._services.get(name)
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all registered services"""
        return self._services.copy()
    
    def initialize_all(self) -> bool:
        """Initialize all singleton services"""
        try:
            # Sort services by dependencies
            sorted_services = self._sort_by_dependencies()
            
            for service_name in sorted_services:
                service_info = self._services[service_name]
                if service_info.singleton and not service_info.initialized:
                    self.resolve(service_name)
                    self._initialization_order.append(service_name)
            
            self._logger.info(f"Initialized {len(sorted_services)} services")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize services: {e}")
            return False
    
    def _sort_by_dependencies(self) -> list:
        """Sort services by their dependencies (topological sort)"""
        # Simple dependency resolution - services with no dependencies first
        no_deps = []
        with_deps = []
        
        for name, service_info in self._services.items():
            if not service_info.dependencies:
                no_deps.append(name)
            else:
                with_deps.append(name)
        
        # For now, just return no-deps first, then with-deps
        # In a full implementation, you'd do proper topological sorting
        return no_deps + with_deps
    
    async def shutdown_all(self):
        """Shutdown all services in reverse initialization order"""
        shutdown_order = list(reversed(self._initialization_order))
        
        for service_name in shutdown_order:
            try:
                service_info = self._services[service_name]
                if service_info.instance and hasattr(service_info.instance, 'shutdown'):
                    if hasattr(service_info.instance.shutdown, '__call__'):
                        if hasattr(service_info.instance, '__aenter__'):  # async context manager
                            await service_info.instance.shutdown()
                        else:
                            service_info.instance.shutdown()
                    
                self._logger.debug(f"Shutdown service: {service_name}")
                
            except Exception as e:
                self._logger.error(f"Error shutting down service '{service_name}': {e}")
        
        self._logger.info("All services shutdown completed")
    
    def clear(self):
        """Clear all registered services"""
        self._services.clear()
        self._initialization_order.clear()
        self._logger.debug("Service container cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get container status"""
        initialized_count = sum(1 for s in self._services.values() if s.initialized)
        
        return {
            'total_services': len(self._services),
            'initialized_services': initialized_count,
            'initialization_order': self._initialization_order.copy(),
            'services': {
                name: {
                    'type': info.service_type.__name__,
                    'singleton': info.singleton,
                    'initialized': info.initialized,
                    'created_at': info.created_at.isoformat() if info.created_at else None,
                    'dependencies': info.dependencies
                }
                for name, info in self._services.items()
            }
        }


# Global service container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container"""
    return _container


def register_singleton(name: str, service_type: Type[T], factory: Callable[[], T] = None, dependencies: list = None) -> ServiceContainer:
    """Register a singleton service in the global container"""
    return _container.register_singleton(name, service_type, factory, dependencies)


def register_transient(name: str, service_type: Type[T], factory: Callable[[], T] = None, dependencies: list = None) -> ServiceContainer:
    """Register a transient service in the global container"""
    return _container.register_transient(name, service_type, factory, dependencies)


def register_instance(name: str, instance: T) -> ServiceContainer:
    """Register an instance in the global container"""
    return _container.register_instance(name, instance)


def resolve(name: str) -> Any:
    """Resolve a service from the global container"""
    return _container.resolve(name)


def resolve_type(service_type: Type[T]) -> T:
    """Resolve a service by type from the global container"""
    return _container.resolve_type(service_type)


# Example usage and testing
if __name__ == "__main__":
    # Example service classes
    class DatabaseService:
        def __init__(self):
            self.connected = True
            print("DatabaseService initialized")
        
        def shutdown(self):
            self.connected = False
            print("DatabaseService shutdown")
    
    class LoggingService:
        def __init__(self):
            print("LoggingService initialized")
        
        def log(self, message: str):
            print(f"LOG: {message}")
    
    class BusinessService:
        def __init__(self, database: DatabaseService, logger: LoggingService):
            self.database = database
            self.logger = logger
            print("BusinessService initialized with dependencies")
        
        def do_work(self):
            self.logger.log("Doing business work...")
            return "Work completed"
    
    # Test the container
    container = ServiceContainer()
    
    # Register services
    container.register_singleton("database", DatabaseService)
    container.register_singleton("logger", LoggingService)
    container.register_singleton("business", BusinessService, dependencies=["database", "logger"])
    
    # Test resolution
    db = container.resolve("database")
    logger_svc = container.resolve("logger")
    business = container.resolve("business")
    
    # Test functionality
    business.do_work()
    
    # Test status
    status = container.get_status()
    print(f"Container status: {status}")
    
    print("Service container test completed successfully!")