"""Spring-style annotations for Flaxon Spring-Boot."""

from typing import Type, List, Optional, Any, Callable
from dataclasses import dataclass, field
import inspect


# ---- Core Annotations ----

class Component:
    """Mark a class as a Spring-style component."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name
    
    def __call__(self, cls: Type) -> Type:
        setattr(cls, '_spring_component', True)
        setattr(cls, '_spring_component_name', self.name or cls.__name__.lower())
        return cls


class Service(Component):
    """Mark a class as a service."""
    
    def __call__(self, cls: Type) -> Type:
        super().__call__(cls)
        setattr(cls, '_spring_service', True)
        return cls


class Repository(Component):
    """Mark a class as a repository."""
    
    def __call__(self, cls: Type) -> Type:
        super().__call__(cls)
        setattr(cls, '_spring_repository', True)
        return cls


class Controller(Component):
    """Mark a class as a controller."""
    
    def __init__(self, name: Optional[str] = None, path: Optional[str] = None):
        super().__init__(name)
        self.path = path
    
    def __call__(self, cls: Type) -> Type:
        super().__call__(cls)
        setattr(cls, '_spring_controller', True)
        setattr(cls, '_spring_controller_path', self.path)
        return cls


class RestController(Controller):
    """Mark a class as a REST controller."""
    
    def __call__(self, cls: Type) -> Type:
        super().__call__(cls)
        setattr(cls, '_spring_rest_controller', True)
        return cls


class Autowired:
    """Mark a field or method for dependency injection."""
    
    def __init__(self, required: bool = True, name: Optional[str] = None):
        self.required = required
        self.name = name
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_autowired', True)
        setattr(target, '_spring_autowired_name', self.name)
        setattr(target, '_spring_autowired_required', self.required)
        return target


class Value:
    """Inject a property value."""
    
    def __init__(self, key: str, default: Any = None):
        self.key = key
        self.default = default
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_value', True)
        setattr(target, '_spring_value_key', self.key)
        setattr(target, '_spring_value_default', self.default)
        return target


class ComponentScan:
    """Enable component scanning."""
    
    def __init__(self, packages: Optional[List[str]] = None):
        self.packages = packages or []
    
    def __call__(self, cls: Type) -> Type:
        setattr(cls, '_spring_component_scan', True)
        setattr(cls, '_spring_component_scan_packages', self.packages)
        return cls


class Configuration:
    """Mark a class as a configuration class."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name
    
    def __call__(self, cls: Type) -> Type:
        setattr(cls, '_spring_configuration', True)
        setattr(cls, '_spring_configuration_name', self.name)
        return cls


class Bean:
    """Mark a method as a bean factory."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name
    
    def __call__(self, func: Callable) -> Callable:
        setattr(func, '_spring_bean', True)
        setattr(func, '_spring_bean_name', self.name)
        return func


class Primary:
    """Mark a bean as primary."""
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_primary', True)
        return target


class Qualifier:
    """Qualify a bean by name."""
    
    def __init__(self, name: str):
        self.name = name
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_qualifier', self.name)
        return target


class Lazy:
    """Mark a bean as lazy-initialized."""
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_lazy', True)
        return target


class Scope:
    """Set bean scope."""
    
    def __init__(self, scope: str):
        self.scope = scope
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_scope', self.scope)
        return target


# ---- Component Scanner ----

class ComponentScanner:
    """Scan for components in packages."""
    
    def __init__(
        self,
        context: Any,
        profile_manager: Any,
        aspect_registry: Any = None,
        rest_registry: Any = None,
        repository_registry: Any = None,
    ):
        self.context = context
        self.profile_manager = profile_manager
        self.aspect_registry = aspect_registry
        self.rest_registry = rest_registry
        self.repository_registry = repository_registry
        self.last_error: Optional[Exception] = None
    
    def scan(self, packages: List[str]) -> None:
        """Scan packages for components."""
        for package in packages or []:
            self._scan_package(package)
    
    def _scan_package(self, package_name: str) -> None:
        """Scan a single package."""
        import importlib
        import pkgutil
        
        try:
            if package_name in (".", "__main__"):
                package = importlib.import_module("__main__")
                self._scan_module(package)
                return
            package = importlib.import_module(package_name)
            self._scan_module(package)
            package_path = getattr(package, "__path__", None)
            if package_path is None:
                self._scan_module(package)
                return
            
            for _, module_name, _ in pkgutil.iter_modules(package_path):
                module = importlib.import_module(f"{package_name}.{module_name}")
                self._scan_module(module)
        except (ImportError, AttributeError) as error:
            # A missing optional package should not prevent the application
            # from starting, but keep the reason available to callers.
            self.last_error = error
    
    def _scan_module(self, module: Any) -> None:
        """Scan a module for components."""
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module.__name__:
                self._register_component(obj)
    
    def _register_component(self, cls: Type) -> None:
        """Register a component class."""
        if not any(
            hasattr(cls, marker)
            for marker in (
                '_spring_component',
                '_spring_aspect',
                '_spring_repository',
                '_spring_rest_controller',
            )
        ):
            return
        
        # Check profile
        if hasattr(cls, '_spring_profile'):
            profiles = getattr(cls, '_spring_profile')
            if not self.profile_manager.is_profile_active(profiles):
                return
        
        # Register the component
        from .container import BeanDefinition
        name = getattr(cls, '_spring_component_name', cls.__name__.lower())
        
        scope = getattr(cls, '_spring_scope', 'singleton')
        from .container import BeanScope
        if isinstance(scope, str):
            try:
                scope = BeanScope(scope.lower())
            except ValueError:
                scope = BeanScope.SINGLETON

        definition = BeanDefinition(
            name=name,
            bean_type=cls,
            scope=scope,
            primary=getattr(cls, '_spring_primary', False),
            lazy=getattr(cls, '_spring_lazy', False),
        )
        if not self.context.has_bean(name):
            self.context.register_bean_definition(definition)

        if self.aspect_registry is not None and getattr(cls, '_spring_aspect', False):
            self.aspect_registry.register(cls)
        if self.repository_registry is not None and getattr(cls, '_spring_repository', False):
            self.repository_registry.register(cls)
        if self.rest_registry is not None and getattr(cls, '_spring_rest_controller', False):
            self.rest_registry.register(
                cls,
                getattr(cls, '_spring_controller_path', None) or "",
            )