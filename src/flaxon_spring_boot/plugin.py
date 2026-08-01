"""Spring Boot plugin for Flaxon."""

import os
from typing import Optional, Dict, Any, List, Type, Callable
from dataclasses import dataclass, field

from flaxon import Flaxon
from flaxon.plugin import Plugin

from .container import ApplicationContext
from .annotations import ComponentScan
from .profiles import ProfileManager, EnableProfiles
from .properties import PropertiesLoader, ConfigurationPropertiesBinder
from .autoconfigure import AutoConfigurationRegistry
from .actuator import ActuatorManager, EnableActuator
from .scheduled import ScheduledTaskRunner, EnableScheduling
from .rest import RestControllerRegistry
from .aop import AspectRegistry, EnableAspectJAutoProxy
from .events import EventPublisher, EnableAsync
from .repository import RepositoryRegistry, EnableJpaRepositories


@dataclass
class SpringBootConfig:
    """Configuration for Spring Boot plugin."""
    
    # Base settings
    profiles: List[str] = field(default_factory=lambda: ["default"])
    autoconfigure: bool = True
    component_scan: bool = True
    component_scan_packages: List[str] = field(default_factory=list)
    
    # Feature flags
    actuator_enabled: bool = True
    scheduling_enabled: bool = True
    aop_enabled: bool = True
    async_enabled: bool = True
    repository_enabled: bool = True
    
    # Properties
    properties_files: List[str] = field(default_factory=lambda: [
        "application.yml",
        "application.properties",
    ])
    properties_prefix: str = "spring"
    
    @classmethod
    def from_env(cls) -> "SpringBootConfig":
        """Load configuration from environment variables."""
        def env_bool(name: str, default: bool) -> bool:
            return os.environ.get(name, str(default)).strip().lower() in {
                "1", "true", "yes", "on"
            }

        return cls(
            profiles=[
                profile.strip()
                for profile in os.environ.get("SPRING_PROFILES_ACTIVE", "default").split(",")
                if profile.strip()
            ] or ["default"],
            autoconfigure=env_bool("SPRING_AUTOCONFIGURE", True),
            component_scan=env_bool("SPRING_COMPONENT_SCAN", True),
            actuator_enabled=env_bool("SPRING_ACTUATOR_ENABLED", True),
            scheduling_enabled=env_bool("SPRING_SCHEDULING_ENABLED", True),
            aop_enabled=env_bool("SPRING_AOP_ENABLED", True),
            async_enabled=env_bool("SPRING_ASYNC_ENABLED", True),
            repository_enabled=env_bool("SPRING_REPOSITORY_ENABLED", True),
        )
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "SpringBootConfig":
        """Load configuration from dictionary."""
        def value(*keys: str, default: Any) -> Any:
            for key in keys:
                if key in config:
                    return config[key]
            return default

        def as_bool(raw: Any, default: bool) -> bool:
            if raw is None:
                return default
            if isinstance(raw, bool):
                return raw
            return str(raw).strip().lower() in {"1", "true", "yes", "on"}

        raw_profiles = value(
            "SPRING_PROFILES_ACTIVE",
            "spring.profiles.active",
            default="default",
        )
        profiles = raw_profiles if isinstance(raw_profiles, list) else str(raw_profiles).split(",")
        return cls(
            profiles=[str(profile).strip() for profile in profiles if str(profile).strip()] or ["default"],
            autoconfigure=as_bool(value("SPRING_AUTOCONFIGURE", "spring.autoconfigure", default=True), True),
            component_scan=as_bool(value("SPRING_COMPONENT_SCAN", "spring.component-scan", default=True), True),
            actuator_enabled=as_bool(value("SPRING_ACTUATOR_ENABLED", "spring.actuator.enabled", default=True), True),
            scheduling_enabled=as_bool(value("SPRING_SCHEDULING_ENABLED", "spring.scheduling.enabled", default=True), True),
            aop_enabled=as_bool(value("SPRING_AOP_ENABLED", "spring.aop.enabled", default=True), True),
            async_enabled=as_bool(value("SPRING_ASYNC_ENABLED", "spring.async.enabled", default=True), True),
            repository_enabled=as_bool(value("SPRING_REPOSITORY_ENABLED", "spring.repository.enabled", default=True), True),
            properties_files=value(
                "SPRING_PROPERTIES_FILES",
                "spring.properties.files",
                default=["application.yml", "application.properties"],
            ),
        )


class SpringBootPlugin(Plugin):
    """
    Spring Boot-style patterns for Flaxon.
    
    Usage:
    
        from flaxon import Flaxon
        from flaxon_spring_boot import SpringBootPlugin
        
        app = Flaxon("my-app")
        
        # Basic usage
        app.plugins.load_plugin(SpringBootPlugin())
        
        # With custom configuration
        app.plugins.load_plugin(SpringBootPlugin(
            profiles=["dev"],
            autoconfigure=True,
            actuator_enabled=True,
        ))
    """
    
    name = "spring-boot"
    version = "0.1.0"
    description = "Spring Boot-style patterns for Flaxon"
    author = "Aldane Hutchinson"
    requires = []
    
    def __init__(
        self,
        profiles: Optional[List[str]] = None,
        autoconfigure: Optional[bool] = None,
        component_scan: Optional[bool] = None,
        component_scan_packages: Optional[List[str]] = None,
        actuator_enabled: Optional[bool] = None,
        scheduling_enabled: Optional[bool] = None,
        aop_enabled: Optional[bool] = None,
        async_enabled: Optional[bool] = None,
        repository_enabled: Optional[bool] = None,
        properties_files: Optional[List[str]] = None,
        config: Optional[SpringBootConfig] = None,
    ):
        """
        Initialize Spring Boot plugin.
        
        Args:
            profiles: Active profiles
            autoconfigure: Enable auto-configuration
            component_scan: Enable component scanning
            component_scan_packages: Packages to scan for components
            actuator_enabled: Enable actuator endpoints
            scheduling_enabled: Enable scheduled tasks
            aop_enabled: Enable AOP
            async_enabled: Enable async event processing
            repository_enabled: Enable repository support
            properties_files: Properties files to load
            config: SpringBootConfig instance
        """
        # Load config
        if config:
            self.config = config
        else:
            env_config = SpringBootConfig.from_env()
            self.config = SpringBootConfig(
                profiles=profiles or env_config.profiles,
                autoconfigure=autoconfigure if autoconfigure is not None else env_config.autoconfigure,
                component_scan=component_scan if component_scan is not None else env_config.component_scan,
                component_scan_packages=component_scan_packages or env_config.component_scan_packages,
                actuator_enabled=actuator_enabled if actuator_enabled is not None else env_config.actuator_enabled,
                scheduling_enabled=scheduling_enabled if scheduling_enabled is not None else env_config.scheduling_enabled,
                aop_enabled=aop_enabled if aop_enabled is not None else env_config.aop_enabled,
                async_enabled=async_enabled if async_enabled is not None else env_config.async_enabled,
                repository_enabled=repository_enabled if repository_enabled is not None else env_config.repository_enabled,
                properties_files=properties_files or env_config.properties_files,
            )
        
        # Initialize components
        self.application_context = ApplicationContext()
        self.profile_manager = ProfileManager(self.config.profiles)
        self.properties_loader = PropertiesLoader()
        self.application_context.properties_loader = self.properties_loader
        self.property_binder = ConfigurationPropertiesBinder()
        self.auto_config_registry = AutoConfigurationRegistry()
        self.actuator_manager = ActuatorManager()
        self.scheduled_task_runner = ScheduledTaskRunner()
        self.rest_registry = RestControllerRegistry()
        self.aspect_registry = AspectRegistry()
        self.event_publisher = EventPublisher()
        self.repository_registry = RepositoryRegistry()
        
        # Store app reference
        self._app = None
        self._initialized = False
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SpringBootPlugin":
        """Create SpringBootPlugin from Flaxon config."""
        plugin_config = SpringBootConfig.from_dict(config)
        return cls(config=plugin_config)
    
    def setup(self, app: Flaxon) -> None:
        """Setup the plugin with the Flaxon application."""
        self._app = app
        app.state.spring_boot = self
        
        # Set up application context
        self.application_context.set_app(app)
        
        # Load properties
        self._load_properties()
        
        # Set active profiles
        self.profile_manager.set_active_profiles(self.config.profiles)
        
        # Register auto-configurations
        if self.config.autoconfigure:
            self._register_auto_configurations()
        
        # Scan components
        if self.config.component_scan:
            self._scan_components()
        
        # Initialize AOP
        if self.config.aop_enabled:
            self._init_aop()
        
        # Initialize repositories
        if self.config.repository_enabled:
            self._init_repositories()
        
        # Initialize REST controllers
        self._init_rest_controllers()
        
        # Initialize scheduled tasks
        if self.config.scheduling_enabled:
            self._init_scheduled_tasks()
        
        # Initialize actuator
        if self.config.actuator_enabled:
            self._init_actuator()
        
        # Initialize async event processing
        if self.config.async_enabled:
            self._init_async()
        
        self._initialized = True
    
    def _load_properties(self) -> None:
        """Load properties from files."""
        for file_path in self.config.properties_files:
            if os.path.exists(file_path):
                self.properties_loader.load_file(file_path)
        
        # Bind configuration properties
        self.property_binder.bind_all(self.application_context, self.properties_loader)
    
    def _register_auto_configurations(self) -> None:
        """Register auto-configurations."""
        auto_configs = self.auto_config_registry.discover()
        for config_class in auto_configs:
            if self._should_apply_auto_config(config_class):
                self.auto_config_registry.apply(config_class, self.application_context)
    
    def _should_apply_auto_config(self, config_class: Type) -> bool:
        """Check if an auto-configuration should be applied."""
        # Check conditions
        conditions = getattr(
            config_class,
            "_spring_auto_configuration_conditions",
            getattr(config_class, "conditions", []),
        )
        for condition in conditions:
            if not condition.matches(self.application_context):
                return False
        return True
    
    def _scan_components(self) -> None:
        """Scan for components."""
        packages = self.config.component_scan_packages or ["."]
        from .annotations import ComponentScanner
        scanner = ComponentScanner(
            self.application_context,
            self.profile_manager,
            aspect_registry=self.aspect_registry,
            rest_registry=self.rest_registry,
            repository_registry=self.repository_registry,
        )
        scanner.scan(packages)
    
    def _init_aop(self) -> None:
        """Initialize AOP."""
        from .aop import AspectWeaver
        weaver = AspectWeaver(self.application_context, self.aspect_registry)
        weaver.weave()
    
    def _init_repositories(self) -> None:
        """Initialize repositories."""
        from .repository import RepositoryInitializer
        initializer = RepositoryInitializer(self.application_context, self.repository_registry)
        initializer.initialize()
    
    def _init_rest_controllers(self) -> None:
        """Initialize REST controllers."""
        from .rest import RestControllerRegistrar
        registrar = RestControllerRegistrar(self.application_context, self.rest_registry, self._app)
        registrar.register()
    
    def _init_scheduled_tasks(self) -> None:
        """Initialize scheduled tasks."""
        from .scheduled import ScheduledTaskInitializer
        initializer = ScheduledTaskInitializer(
            self.application_context,
            self.scheduled_task_runner,
            self._app
        )
        initializer.initialize()
        self.scheduled_task_runner.start()
    
    def _init_actuator(self) -> None:
        """Initialize actuator endpoints."""
        from .actuator import ActuatorRegistrar
        registrar = ActuatorRegistrar(
            self.application_context,
            self.actuator_manager,
            self._app
        )
        registrar.register()
    
    def _init_async(self) -> None:
        """Initialize async event processing."""
        from .events import AsyncEventProcessor
        self.event_publisher.processor = AsyncEventProcessor(self.application_context)
    
    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass
    
    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        if self.scheduled_task_runner:
            self.scheduled_task_runner.stop()
    
    def on_startup(self) -> None:
        """Called on application startup."""
        pass
    
    def on_shutdown(self) -> None:
        """Called on application shutdown."""
        if self.scheduled_task_runner:
            self.scheduled_task_runner.stop()
    
    def get_bean(self, name: str, required_type: Optional[Type] = None) -> Any:
        """Get a bean from the application context."""
        return self.application_context.get_bean(name, required_type)
    
    def get_beans(self, bean_type: Type) -> List[Any]:
        """Get all beans of a type."""
        return self.application_context.get_beans(bean_type)
    
    def publish_event(self, event: Any) -> None:
        """Publish an event."""
        self.event_publisher.publish_event(event)
    
    def is_initialized(self) -> bool:
        """Check if the plugin is initialized."""
        return self._initialized
    
    def get_active_profiles(self) -> List[str]:
        """Get active profiles."""
        return self.profile_manager.get_active_profiles()
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value."""
        return self.properties_loader.get(key, default)
    
    def get_required_property(self, key: str) -> Any:
        """Get a required property value."""
        return self.properties_loader.get_required(key)