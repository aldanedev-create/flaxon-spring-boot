"""Application properties loader for Spring Boot."""

import os
from typing import Any, Dict, Optional, List
from pathlib import Path


class PropertiesLoader:
    """Load properties from application.yml and application.properties."""
    
    def __init__(self):
        self._properties: Dict[str, Any] = {}
    
    def load_file(self, file_path: str) -> None:
        """Load properties from a file."""
        path = Path(file_path)
        if not path.exists():
            return
        
        if path.suffix in ['.yml', '.yaml']:
            self._load_yaml(path)
        elif path.suffix == '.properties':
            self._load_properties(path)
    
    def _load_yaml(self, path: Path) -> None:
        """Load YAML file."""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    self._flatten(data, '')
        except ImportError as error:
            raise RuntimeError(
                "YAML support requires PyYAML; install pyyaml or use a .properties file"
            ) from error
    
    def _load_properties(self, path: Path) -> None:
        """Load properties file."""
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    self._properties[key.strip()] = value.strip()
    
    def _flatten(self, data: Dict[str, Any], prefix: str) -> None:
        """Flatten nested dictionary."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten(value, full_key)
            else:
                self._properties[full_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a property value."""
        return self._properties.get(key, default)
    
    def get_required(self, key: str) -> Any:
        """Get a required property value."""
        if key not in self._properties:
            raise ValueError(f"Required property '{key}' not found")
        return self._properties[key]
    
    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get an integer property."""
        value = self.get(key)
        if value is None:
            return default
        return int(value)
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get a boolean property."""
        value = self.get(key)
        if value is None:
            return default
        return str(value).lower() in ('true', 'yes', '1')
    
    def get_list(self, key: str, default: Optional[List[str]] = None) -> Optional[List[str]]:
        """Get a list property."""
        value = self.get(key)
        if value is None:
            return default
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',')]
        return [str(value)]
    
    def has(self, key: str) -> bool:
        """Check if a property exists."""
        return key in self._properties
    
    def to_dict(self) -> Dict[str, Any]:
        """Get all properties."""
        return dict(self._properties)


class ConfigurationProperties:
    """Configuration properties annotation."""
    
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_configuration_properties', True)
        setattr(cls, '_spring_configuration_properties_prefix', self.prefix)
        return cls


class EnableConfigurationProperties:
    """Enable configuration properties."""
    
    def __init__(self, *classes: Any):
        self.classes = list(classes)
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_configuration_properties', self.classes)
        return cls


class PropertySource:
    """Property source annotation."""
    
    def __init__(self, value: str):
        self.value = value
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_property_source', self.value)
        return cls


class ConfigurationPropertiesBinder:
    """Bind configuration properties to classes."""
    
    def __init__(self):
        self._bindings: Dict[str, Any] = {}
    
    def bind_all(self, context: Any, loader: PropertiesLoader) -> None:
        """Bind all configuration properties."""
        for name in list(context.get_bean_names()):
            definition = context.get_bean_definition(name)
            bean_type = definition.bean_type if definition else type(context.get_bean(name))
            if not getattr(bean_type, '_spring_configuration_properties', False):
                continue
            prefix = getattr(bean_type, '_spring_configuration_properties_prefix', '')
            instance = context.get_bean(name)
            self.bind_dict(instance, prefix, loader.to_dict())
            self._bindings[name] = instance
    
    def bind(self, cls: Any, prefix: str, properties: Dict[str, Any]) -> Any:
        """Bind properties to a class instance."""
        instance = cls()
        
        for key, value in properties.items():
            if key.startswith(prefix):
                attr = key[len(prefix):].lstrip('.')
                if hasattr(instance, attr) or attr in getattr(type(instance), "__annotations__", {}):
                    setattr(instance, attr, value)
        
        return instance
    
    def bind_dict(self, instance: Any, prefix: str, properties: Dict[str, Any]) -> None:
        """Bind properties to an existing instance."""
        for key, value in properties.items():
            if key.startswith(prefix):
                attr = key[len(prefix):].lstrip('.')
                if hasattr(instance, attr):
                    setattr(instance, attr, value)