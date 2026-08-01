"""Flaxon Spring-Boot - Spring Boot-style patterns for Flaxon."""

from .plugin import SpringBootPlugin
from .container import ApplicationContext, BeanDefinition, BeanScope
from .annotations import (
    Component,
    Service,
    Repository,
    Controller,
    RestController,
    Autowired,
    Value,
    ComponentScan,
    Configuration,
    Bean,
    Primary,
    Qualifier,
    Lazy,
    Scope,
)
from .rest import (
    GetMapping,
    PostMapping,
    PutMapping,
    DeleteMapping,
    PatchMapping,
    RequestMapping,
    RequestBody,
    RequestParam,
    PathVariable,
    RequestHeader,
)
from .transactional import Transactional
from .scheduled import Scheduled, EnableScheduling
from .aop import Aspect, Before, After, Around, AfterReturning, AfterThrowing, Pointcut, EnableAspectJAutoProxy
from .profiles import Profile, EnableProfiles
from .properties import ConfigurationProperties, EnableConfigurationProperties, PropertySource
from .actuator import EnableActuator, HealthIndicator, InfoContributor
from .repository import EnableJpaRepositories, Query, Modifying
from .events import Event, EventListener, ApplicationEventPublisher, EnableAsync
from .autoconfigure import AutoConfiguration, ConditionalOnClass, ConditionalOnMissingClass, ConditionalOnProperty, ConditionalOnBean, ConditionalOnMissingBean

__all__ = [
    # Plugin
    "SpringBootPlugin",
    
    # Container
    "ApplicationContext",
    "BeanDefinition",
    "BeanScope",
    
    # Annotations
    "Component",
    "Service",
    "Repository",
    "Controller",
    "RestController",
    "Autowired",
    "Value",
    "ComponentScan",
    "Configuration",
    "Bean",
    "Primary",
    "Qualifier",
    "Lazy",
    "Scope",
    
    # REST
    "GetMapping",
    "PostMapping",
    "PutMapping",
    "DeleteMapping",
    "PatchMapping",
    "RequestMapping",
    "RequestBody",
    "RequestParam",
    "PathVariable",
    "RequestHeader",
    
    # Transactional
    "Transactional",
    
    # Scheduled
    "Scheduled",
    "EnableScheduling",
    
    # AOP
    "Aspect",
    "Before",
    "After",
    "Around",
    "AfterReturning",
    "AfterThrowing",
    "Pointcut",
    "EnableAspectJAutoProxy",
    
    # Profiles
    "Profile",
    "EnableProfiles",
    
    # Properties
    "ConfigurationProperties",
    "EnableConfigurationProperties",
    "PropertySource",
    
    # Actuator
    "EnableActuator",
    "HealthIndicator",
    "InfoContributor",
    
    # Repository
    "Repository",
    "EnableJpaRepositories",
    "Query",
    "Modifying",
    
    # Events
    "Event",
    "EventListener",
    "ApplicationEventPublisher",
    "EnableAsync",
    
    # Auto-configuration
    "AutoConfiguration",
    "ConditionalOnClass",
    "ConditionalOnMissingClass",
    "ConditionalOnProperty",
    "ConditionalOnBean",
    "ConditionalOnMissingBean",
]

__version__ = "0.1.0"