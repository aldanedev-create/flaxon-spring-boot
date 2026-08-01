"""Repository support for Spring Boot."""

import inspect
from types import MethodType
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field


class Repository:
    """Repository annotation."""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name
    
    def __call__(self, cls: Type) -> Type:
        setattr(cls, '_spring_repository', True)
        setattr(cls, '_spring_repository_name', self.name)
        setattr(cls, '_spring_component', True)
        setattr(cls, '_spring_component_name', self.name or cls.__name__.lower())
        return cls


class EnableJpaRepositories:
    """Enable JPA repositories."""
    
    def __init__(self, base_package: Optional[str] = None):
        self.base_package = base_package
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_jpa_repositories', True)
        setattr(cls, '_spring_jpa_base_package', self.base_package)
        return cls


class Query:
    """Query annotation for repository methods."""
    
    def __init__(self, value: str):
        self.value = value
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_query', True)
        setattr(target, '_spring_query_value', self.value)
        return target


class Modifying:
    """Modifying annotation for repository methods."""
    
    def __init__(self, flush_automatically: bool = True):
        self.flush_automatically = flush_automatically
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_modifying', True)
        setattr(target, '_spring_modifying_flush', self.flush_automatically)
        return target


class RepositoryRegistry:
    """Registry for repositories."""
    
    def __init__(self):
        self._repositories: Dict[str, Type] = {}
    
    def register(self, repo_class: Type) -> None:
        """Register a repository."""
        name = getattr(
            repo_class,
            '_spring_repository_name',
            None,
        ) or getattr(repo_class, '_spring_component_name', repo_class.__name__.lower())
        self._repositories[name] = repo_class
    
    def get(self, name: str) -> Optional[Type]:
        """Get a repository by name."""
        return self._repositories.get(name)
    
    def get_all(self) -> Dict[str, Type]:
        """Get all repositories."""
        return self._repositories


class RepositoryInitializer:
    """Initialize repositories."""
    
    def __init__(self, context: Any, registry: RepositoryRegistry):
        self.context = context
        self.registry = registry
    
    def initialize(self) -> None:
        """Initialize all repositories."""
        for name, repo_class in self.registry.get_all().items():
            self._initialize_repository(name, repo_class)
    
    def _initialize_repository(self, name: str, repo_class: Type) -> None:
        """Initialize a single repository."""
        # Check if repository has methods that need to be auto-implemented
        if hasattr(repo_class, '_spring_query_methods'):
            # Auto-implement query methods
            pass
        
        # Create repository instance
        instance = repo_class()
        proxy = RepositoryProxy(repo_class, self.context)
        proxy._instance = instance
        proxy._auto_implement_methods()
        instance = proxy.get_instance()
        
        self.context.register_singleton(name, instance)


class RepositoryProxy:
    """Proxy for repository with auto-implemented methods."""
    
    def __init__(self, repo_class: Type, context: Any):
        self.repo_class = repo_class
        self.context = context
        self._instance = None
    
    def get_instance(self) -> Any:
        """Get the repository instance."""
        if self._instance is None:
            self._instance = self.repo_class()
            self._auto_implement_methods()
        return self._instance
    
    def _auto_implement_methods(self) -> None:
        """Auto-implement repository methods."""
        for name, method in inspect.getmembers(self.repo_class, inspect.isfunction):
            if hasattr(method, '_spring_query'):
                self._implement_query_method(name, method)
    
    def _implement_query_method(self, name: str, method: Callable) -> None:
        """Implement a query method."""
        query = getattr(method, '_spring_query_value')
        
        async def query_method(instance, *args, **kwargs):
            # Execute query
            # This would use the underlying data source
            return []
        
        setattr(self._instance, name, MethodType(query_method, self._instance))