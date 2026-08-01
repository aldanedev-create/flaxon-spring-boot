"""Type definitions for Flaxon Spring-Boot."""

from typing import Any, Dict, List, Optional, Type, Union, Callable, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


# ---- Enums ----

class BeanScope(Enum):
    """Bean scope types."""
    SINGLETON = "singleton"
    PROTOTYPE = "prototype"
    REQUEST = "request"
    SESSION = "session"
    APPLICATION = "application"


class Propagation(Enum):
    """Transaction propagation types."""
    REQUIRED = "REQUIRED"
    REQUIRES_NEW = "REQUIRES_NEW"
    MANDATORY = "MANDATORY"
    NEVER = "NEVER"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    SUPPORTS = "SUPPORTS"


class Isolation(Enum):
    """Transaction isolation levels."""
    DEFAULT = "DEFAULT"
    READ_UNCOMMITTED = "READ_UNCOMMITTED"
    READ_COMMITTED = "READ_COMMITTED"
    REPEATABLE_READ = "REPEATABLE_READ"
    SERIALIZABLE = "SERIALIZABLE"


class AdviceType(Enum):
    """AOP advice types."""
    BEFORE = "before"
    AFTER = "after"
    AROUND = "around"
    AFTER_RETURNING = "after_returning"
    AFTER_THROWING = "after_throwing"


# ---- Data Classes ----

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
    description: Optional[str] = None
    order: int = 0


@dataclass
class ComponentScanDefinition:
    """Component scan definition."""
    packages: List[str] = field(default_factory=list)
    exclude_filters: List[Type] = field(default_factory=list)
    include_filters: List[Type] = field(default_factory=list)


@dataclass
class PropertySourceDefinition:
    """Property source definition."""
    name: str
    location: str
    optional: bool = False
    priority: int = 0


@dataclass
class PropertyValue:
    """Property value with source tracking."""
    key: str
    value: Any
    source: Optional[str] = None
    line: Optional[int] = None
    type: str = "string"


@dataclass
class ScheduledTaskConfig:
    """Scheduled task configuration."""
    cron: Optional[str] = None
    fixed_delay: Optional[int] = None
    fixed_rate: Optional[int] = None
    initial_delay: Optional[int] = None
    timezone: Optional[str] = None
    zone: Optional[str] = None


@dataclass
class TransactionConfig:
    """Transaction configuration."""
    propagation: Propagation = Propagation.REQUIRED
    isolation: Isolation = Isolation.DEFAULT
    timeout: Optional[int] = None
    read_only: bool = False
    rollback_for: List[Type[Exception]] = field(default_factory=list)
    no_rollback_for: List[Type[Exception]] = field(default_factory=list)


@dataclass
class PointcutDefinition:
    """Pointcut definition."""
    expression: str
    method: Optional[Callable] = None
    class_name: Optional[str] = None
    method_name: Optional[str] = None


@dataclass
class AdviceDefinition:
    """Advice definition."""
    type: AdviceType
    pointcut: PointcutDefinition
    method: Callable
    order: int = 0
    returning: Optional[str] = None
    throwing: Optional[str] = None


@dataclass
class AspectDefinition:
    """Aspect definition."""
    name: str
    class_type: Type
    advice: List[AdviceDefinition] = field(default_factory=list)
    order: int = 0
    singleton: bool = True


@dataclass
class RestControllerDefinition:
    """REST controller definition."""
    path: str
    class_type: Type
    methods: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EndpointDefinition:
    """Endpoint definition."""
    path: str
    method: str
    handler: Callable
    consumes: Optional[str] = None
    produces: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EventListenerDefinition:
    """Event listener definition."""
    event_type: Type
    method: Callable
    condition: Optional[str] = None
    async_mode: bool = False
    order: int = 0


# ---- Type Aliases ----

# Bean factory type
BeanFactory = Callable[..., Any]

# Bean type map
BeanTypeMap = Dict[str, Type]

# Bean instance map
BeanInstanceMap = Dict[str, Any]

# Bean definition map
BeanDefinitionMap = Dict[str, BeanDefinition]

# Property map
PropertyMap = Dict[str, Any]

# Health status type
HealthStatus = Dict[str, Any]

# Metrics type
MetricsMap = Dict[str, Any]

# Info type
InfoMap = Dict[str, Any]

# Routes type
RoutesMap = Dict[str, str]

# ---- Type Unions ----

# Bean name or type
BeanIdentifier = Union[str, Type]

# Property value types
PropertyValueTypes = Union[str, int, float, bool, List[str], Dict[str, Any], None]

# Configuration value types
ConfigValueTypes = Union[str, int, float, bool, List[Any], Dict[str, Any], None]

# ---- Protocols ----

from typing import Protocol, runtime_checkable


@runtime_checkable
class BeanProvider(Protocol):
    """Protocol for bean providers."""
    
    def get_bean(self, name: str, required_type: Optional[Type] = None) -> Any:
        """Get a bean by name."""
        ...
    
    def get_beans(self, bean_type: Type) -> List[Any]:
        """Get all beans of a type."""
        ...


@runtime_checkable
class ApplicationContextProvider(Protocol):
    """Protocol for application context providers."""
    
    def get_context(self) -> Any:
        """Get the application context."""
        ...


@runtime_checkable
class HealthIndicator(Protocol):
    """Protocol for health indicators."""
    
    def health(self) -> Dict[str, Any]:
        """Return health status."""
        ...


@runtime_checkable
class InfoContributor(Protocol):
    """Protocol for info contributors."""
    
    def contribute(self) -> Dict[str, Any]:
        """Contribute info."""
        ...


# ---- Constants ----

DEFAULT_PROFILES = ["default"]
DEFAULT_PROPERTIES_FILES = ["application.yml", "application.properties"]
DEFAULT_ACTUATOR_PREFIX = "/actuator"

# ---- Error Types ----

class BeanNotFoundError(Exception):
    """Exception raised when a bean is not found."""
    pass


class BeanCreationError(Exception):
    """Exception raised when bean creation fails."""
    pass


class CyclicDependencyError(Exception):
    """Exception raised when a cyclic dependency is detected."""
    pass


class PropertyNotFoundError(Exception):
    """Exception raised when a property is not found."""
    pass


class TransactionError(Exception):
    """Exception raised when a transaction operation fails."""
    pass


class AspectError(Exception):
    """Exception raised when aspect weaving fails."""
    pass