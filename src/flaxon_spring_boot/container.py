"""Dependency Injection container / ApplicationContext for Spring Boot."""

import inspect
from typing import Any, Dict, List, Optional, Type, Callable, Set, get_type_hints
from enum import Enum
from dataclasses import dataclass, field


class BeanScope(Enum):
    """Bean scope types."""
    SINGLETON = "singleton"
    PROTOTYPE = "prototype"
    REQUEST = "request"


@dataclass
class BeanDefinition:
    """Bean definition metadata."""
    name: str
    bean_type: Type
    factory: Optional[Callable] = None
    scope: BeanScope = BeanScope.SINGLETON
    primary: bool = False
    lazy: bool = False
    dependencies: Set[str] = field(default_factory=set)
    properties: Dict[str, Any] = field(default_factory=dict)


class ApplicationContext:
    """
    Spring-style ApplicationContext for dependency injection.
    """
    
    def __init__(self):
        self._beans: Dict[str, Any] = {}
        self._bean_definitions: Dict[str, BeanDefinition] = {}
        self._bean_types: Dict[Type, List[str]] = {}
        self._singletons: Dict[str, Any] = {}
        self._prototypes: Dict[str, Callable] = {}
        self._app = None
        self._initialized = False
    
    def set_app(self, app: Any) -> None:
        """Set the Flaxon application instance."""
        self._app = app
    
    def get_app(self) -> Any:
        """Get the Flaxon application instance."""
        return self._app
    
    def register_bean_definition(self, definition: BeanDefinition) -> None:
        """Register a bean definition."""
        if isinstance(definition.scope, str):
            try:
                definition.scope = BeanScope(definition.scope.lower())
            except ValueError:
                definition.scope = BeanScope.SINGLETON
        old_definition = self._bean_definitions.get(definition.name)
        if old_definition and old_definition.bean_type in self._bean_types:
            self._bean_types[old_definition.bean_type] = [
                name for name in self._bean_types[old_definition.bean_type]
                if name != definition.name
            ]
        self._bean_definitions[definition.name] = definition
        if definition.bean_type not in self._bean_types:
            self._bean_types[definition.bean_type] = []
        if definition.name not in self._bean_types[definition.bean_type]:
            self._bean_types[definition.bean_type].append(definition.name)
    
    def register_bean(self, name: str, bean: Any, bean_type: Optional[Type] = None) -> None:
        """Register a bean instance."""
        self._beans[name] = bean
        bean_type = bean_type or type(bean)
        if bean_type:
            if bean_type not in self._bean_types:
                self._bean_types[bean_type] = []
            if name not in self._bean_types[bean_type]:
                self._bean_types[bean_type].append(name)
    
    def get_bean(self, name: str, required_type: Optional[Type] = None) -> Any:
        """Get a bean by name."""
        if name in self._beans:
            return self._beans[name]
        
        # Check if it's a bean definition that needs to be created
        if name in self._bean_definitions:
            definition = self._bean_definitions[name]
            bean = self._create_bean(definition)
            if definition.scope == BeanScope.SINGLETON:
                self._beans[name] = bean
            return bean
        
        # Try by type
        if required_type and required_type in self._bean_types:
            names = self._bean_types[required_type]
            if names:
                # Return primary if available
                primary = [
                    n for n in names
                    if self._bean_definitions.get(n, BeanDefinition(
                        name=n, bean_type=type(self._beans.get(n))
                    )).primary
                ]
                target_name = primary[0] if primary else names[0]
                return self.get_bean(target_name, required_type)
        
        raise ValueError(f"Bean '{name}' not found")
    
    def get_beans(self, bean_type: Type) -> List[Any]:
        """Get all beans of a type."""
        result = []
        for name in self._bean_types.get(bean_type, []):
            result.append(self.get_bean(name, bean_type))
        return result
    
    def _create_bean(self, definition: BeanDefinition) -> Any:
        """Create a bean instance from a definition."""
        if definition.factory:
            # Factory method
            factory = definition.factory
            if inspect.iscoroutinefunction(factory):
                raise ValueError(
                    f"Async factory for bean '{definition.name}' cannot be "
                    "resolved by the synchronous application context"
                )
            return factory()
        
        # Constructor injection
        bean_type = definition.bean_type
        init_params = inspect.signature(bean_type.__init__).parameters
        
        # Find autowired dependencies
        args = []
        kwargs = {}
        for param_name, param in init_params.items():
            if param_name == 'self':
                continue
            annotation = param.annotation
            try:
                annotation = get_type_hints(bean_type.__init__).get(param_name, annotation)
            except (NameError, TypeError):
                pass
            if annotation != inspect.Parameter.empty:
                try:
                    annotation_name = getattr(annotation, '__name__', str(annotation))
                    dep = self.get_bean(annotation_name, annotation)
                    args.append(dep)
                except ValueError:
                    # Try by type
                    try:
                        dep = self.get_bean_by_type(annotation)
                        args.append(dep)
                    except ValueError:
                        pass
            elif param.default == inspect.Parameter.empty:
                # Required parameter - try to find by name
                try:
                    dep = self.get_bean(param_name)
                    args.append(dep)
                except ValueError:
                    pass
        
        try:
            return bean_type(*args, **kwargs)
        except TypeError as error:
            raise ValueError(
                f"Could not create bean '{definition.name}': {error}"
            ) from error
    
    def get_bean_by_type(self, bean_type: Type) -> Any:
        """Get a bean by type."""
        if bean_type in self._bean_types:
            names = self._bean_types[bean_type]
            if names:
                primary = [
                    name for name in names
                    if self._bean_definitions.get(name)
                    and self._bean_definitions[name].primary
                ]
                return self.get_bean((primary or names)[0], bean_type)
        for name, bean in self._beans.items():
            if isinstance(bean, bean_type):
                return bean
        raise ValueError(f"No bean of type '{bean_type.__name__}' found")
    
    def has_bean(self, name: str) -> bool:
        """Check if a bean exists."""
        return name in self._beans or name in self._bean_definitions
    
    def has_bean_type(self, bean_type: Type) -> bool:
        """Check if a bean type exists."""
        return bean_type in self._bean_types or any(
            isinstance(bean, bean_type) for bean in self._beans.values()
        )
    
    def get_bean_names(self) -> List[str]:
        """Get all bean names."""
        return list(self._beans.keys()) + list(self._bean_definitions.keys())
    
    def get_bean_types(self) -> Dict[Type, List[str]]:
        """Get all bean types."""
        return self._bean_types
    
    def get_bean_definition(self, name: str) -> Optional[BeanDefinition]:
        """Get a bean definition."""
        return self._bean_definitions.get(name)
    
    def register_singleton(self, name: str, bean: Any) -> None:
        """Register a singleton bean."""
        self._singletons[name] = bean
        self.register_bean(name, bean)
    
    def register_prototype(self, name: str, factory: Callable) -> None:
        """Register a prototype bean factory."""
        self._prototypes[name] = factory
    
    def get_singleton(self, name: str) -> Optional[Any]:
        """Get a singleton bean."""
        return self._singletons.get(name)
    
    def is_initialized(self) -> bool:
        """Check if the context is initialized."""
        return self._initialized
    
    def set_initialized(self, initialized: bool) -> None:
        """Set the initialized state."""
        self._initialized = initialized
    
    def clear(self) -> None:
        """Clear all beans."""
        self._beans.clear()
        self._bean_definitions.clear()
        self._bean_types.clear()
        self._singletons.clear()
        self._prototypes.clear()
        self._initialized = False