"""Auto-configuration support for Spring Boot."""

from typing import Type, List, Any, Dict, Optional
from dataclasses import dataclass, field
import inspect


@dataclass
class AutoConfiguration:
    """Mark a class as an auto-configuration."""
    
    name: str = ""
    before: List[str] = field(default_factory=list)
    after: List[str] = field(default_factory=list)
    conditions: List[Any] = field(default_factory=list)
    
    def __call__(self, cls: Type) -> Type:
        setattr(cls, '_spring_auto_configuration', True)
        setattr(cls, '_spring_auto_configuration_name', self.name or cls.__name__)
        setattr(cls, '_spring_auto_configuration_before', self.before)
        setattr(cls, '_spring_auto_configuration_after', self.after)
        setattr(cls, '_spring_auto_configuration_conditions', self.conditions)
        return cls


class ConditionalOnClass:
    """Conditional on class presence."""
    
    def __init__(self, classes: Optional[List[str]] = None):
        self.classes = classes or []
    
    def matches(self, context: Any) -> bool:
        """Check if the condition matches."""
        import importlib
        for class_name in self.classes:
            try:
                module_name, _, attribute_name = class_name.rpartition(".")
                module = importlib.import_module(module_name or class_name)
                if attribute_name and not hasattr(module, attribute_name):
                    return False
            except ImportError:
                return False
        return True


class ConditionalOnMissingClass:
    """Conditional on class absence."""
    
    def __init__(self, classes: Optional[List[str]] = None):
        self.classes = classes or []
    
    def matches(self, context: Any) -> bool:
        """Check if the condition matches."""
        import importlib
        for class_name in self.classes:
            try:
                module_name, _, attribute_name = class_name.rpartition(".")
                module = importlib.import_module(module_name or class_name)
                if not attribute_name or hasattr(module, attribute_name):
                    return False
            except ImportError:
                pass
        return True


class ConditionalOnProperty:
    """Conditional on property existence."""
    
    def __init__(self, key: str, having_value: Optional[str] = None, match_if_missing: bool = False):
        self.key = key
        self.having_value = having_value
        self.match_if_missing = match_if_missing
    
    def matches(self, context: Any) -> bool:
        """Check if the condition matches."""
        if not hasattr(context, 'properties_loader'):
            return self.match_if_missing
        
        value = context.properties_loader.get(self.key)
        if value is None:
            return self.match_if_missing
        
        if self.having_value is not None:
            return str(value) == self.having_value
        
        return True


class ConditionalOnBean:
    """Conditional on bean presence."""
    
    def __init__(self, types: Optional[List[Type]] = None, names: Optional[List[str]] = None):
        self.types = types or []
        self.names = names or []
    
    def matches(self, context: Any) -> bool:
        """Check if the condition matches."""
        for bean_type in self.types:
            if not context.has_bean_type(bean_type):
                return False
        
        for name in self.names:
            if not context.has_bean(name):
                return False
        
        return True


class ConditionalOnMissingBean:
    """Conditional on bean absence."""
    
    def __init__(self, types: Optional[List[Type]] = None, names: Optional[List[str]] = None):
        self.types = types or []
        self.names = names or []
    
    def matches(self, context: Any) -> bool:
        """Check if the condition matches."""
        for bean_type in self.types:
            if context.has_bean_type(bean_type):
                return False
        
        for name in self.names:
            if context.has_bean(name):
                return False
        
        return True


class AutoConfigurationRegistry:
    """Registry for auto-configurations."""
    
    def __init__(self):
        self._configs: List[Type] = []
    
    def register(self, config: Type) -> None:
        """Register an auto-configuration."""
        if config not in self._configs:
            self._configs.append(config)
    
    def discover(self) -> List[Type]:
        """Discover auto-configurations."""
        import importlib
        import pkgutil
        
        result = list(self._configs)
        
        # Scan for auto-configurations
        try:
            import flaxon_spring_boot
            for _, module_name, _ in pkgutil.iter_modules(flaxon_spring_boot.__path__):
                if module_name.startswith('autoconfigure'):
                    module = importlib.import_module(f"flaxon_spring_boot.{module_name}")
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and hasattr(obj, '_spring_auto_configuration'):
                            if obj not in result:
                                result.append(obj)
        except (ImportError, AttributeError):
            pass
        
        return result
    
    def apply(self, config: Type, context: Any) -> None:
        """Apply an auto-configuration."""
        target = config() if inspect.isclass(config) else config
        if hasattr(target, 'configure'):
            target.configure(context)
        elif hasattr(target, 'get_beans'):
            beans = target.get_beans()
            for name, bean in beans.items():
                context.register_singleton(name, bean)