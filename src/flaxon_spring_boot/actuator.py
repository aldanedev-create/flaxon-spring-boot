"""Actuator support for Spring Boot."""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import inspect


class EnableActuator:
    """Enable actuator endpoints."""
    
    def __init__(self, endpoints: Optional[List[str]] = None):
        self.endpoints = endpoints or ["health", "info", "metrics", "routes"]
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_actuator', True)
        setattr(cls, '_spring_actuator_endpoints', self.endpoints)
        return cls


class HealthIndicator:
    """Health indicator interface."""
    
    async def health(self) -> Dict[str, Any]:
        """Return health status."""
        return {"status": "UP"}


class InfoContributor:
    """Info contributor interface."""
    
    async def contribute(self) -> Dict[str, Any]:
        """Contribute info."""
        return {}


class ActuatorManager:
    """Manage actuator endpoints."""
    
    def __init__(self):
        self._health_indicators: List[HealthIndicator] = []
        self._info_contributors: List[InfoContributor] = []
        self._metrics: Dict[str, Any] = {}
        self._start_time = datetime.now()
    
    def add_health_indicator(self, indicator: HealthIndicator) -> None:
        """Add a health indicator."""
        self._health_indicators.append(indicator)
    
    def add_info_contributor(self, contributor: InfoContributor) -> None:
        """Add an info contributor."""
        self._info_contributors.append(contributor)
    
    def record_metric(self, name: str, value: Any) -> None:
        """Record a metric."""
        self._metrics[name] = value
    
    async def get_health(self) -> Dict[str, Any]:
        """Get health status."""
        status = "UP"
        details = {}
        
        for indicator in self._health_indicators:
            try:
                result = indicator.health()
                if inspect.isawaitable(result):
                    result = await result
                if not isinstance(result, dict):
                    result = {"status": "UP", "details": result}
                if result.get("status") != "UP":
                    status = "DOWN"
                details[indicator.__class__.__name__] = result
            except Exception as e:
                status = "DOWN"
                details[indicator.__class__.__name__] = {"status": "DOWN", "error": str(e)}
        
        return {"status": status, "components": details}
    
    async def get_info(self) -> Dict[str, Any]:
        """Get app info."""
        info = {
            "app": {
                "name": "Flaxon Application",
                "version": "1.0.0",
            }
        }
        
        for contributor in self._info_contributors:
            try:
                result = contributor.contribute()
                if inspect.isawaitable(result):
                    result = await result
                if isinstance(result, dict):
                    info.update(result)
            except Exception:
                pass
        
        return info
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics."""
        return {
            "metrics": self._metrics,
            "uptime": (datetime.now() - self._start_time).total_seconds(),
        }


class ActuatorRegistrar:
    """Register actuator endpoints with Flaxon."""
    
    def __init__(self, context: Any, manager: ActuatorManager, app: Any):
        self.context = context
        self.manager = manager
        self.app = app
    
    def register(self) -> None:
        """Register actuator endpoints."""
        prefix = "/actuator"
        
        @self.app.get(f"{prefix}/health")
        async def health(request):
            return await self.manager.get_health()
        
        @self.app.get(f"{prefix}/info")
        async def info(request):
            return await self.manager.get_info()
        
        @self.app.get(f"{prefix}/metrics")
        async def metrics(request):
            return self.manager.get_metrics()
        
        @self.app.get(f"{prefix}/routes")
        async def routes(request):
            return {"routes": self._get_routes()}
    
    def _get_routes(self) -> List[str]:
        """Get registered routes."""
        routes = []
        if hasattr(self.app, 'router'):
            registered_routes = getattr(
                self.app.router,
                "_routes",
                getattr(self.app.router, "routes", []),
            )
            for route in registered_routes:
                method = getattr(route, "method", None)
                path = getattr(route, "path", None)
                if method is not None and path is not None:
                    routes.append(f"{method} {path}")
        return routes