"""REST controller support for Spring Boot."""

from typing import Any, Dict, List, Optional, Type, Callable
import inspect
import re
from functools import wraps

# ---- Request Mapping Annotations ----

class RequestMapping:
    """Base request mapping annotation."""
    
    def __init__(
        self,
        path: Optional[str] = None,
        method: Optional[str] = None,
        consumes: Optional[str] = None,
        produces: Optional[str] = None,
    ):
        self.path = path
        self.method = method
        self.consumes = consumes
        self.produces = produces

    def __call__(self, target: Any) -> Any:
        """Attach this mapping to a controller class or method."""
        setattr(target, "_spring_mapping", self)
        return target


class GetMapping(RequestMapping):
    """GET request mapping."""
    
    def __init__(self, path: str = ""):
        super().__init__(path=path, method="GET")


class PostMapping(RequestMapping):
    """POST request mapping."""
    
    def __init__(self, path: str = ""):
        super().__init__(path=path, method="POST")


class PutMapping(RequestMapping):
    """PUT request mapping."""
    
    def __init__(self, path: str = ""):
        super().__init__(path=path, method="PUT")


class DeleteMapping(RequestMapping):
    """DELETE request mapping."""
    
    def __init__(self, path: str = ""):
        super().__init__(path=path, method="DELETE")


class PatchMapping(RequestMapping):
    """PATCH request mapping."""
    
    def __init__(self, path: str = ""):
        super().__init__(path=path, method="PATCH")


# ---- Request Parameter Annotations ----

class RequestBody:
    """Mark a parameter as the request body."""
    
    def __init__(self, required: bool = True):
        self.required = required


class RequestParam:
    """Mark a parameter as a request parameter."""
    
    def __init__(self, name: Optional[str] = None, required: bool = True, default: Any = None):
        self.name = name
        self.required = required
        self.default = default


class PathVariable:
    """Mark a parameter as a path variable."""
    
    def __init__(self, name: Optional[str] = None, required: bool = True):
        self.name = name
        self.required = required


class RequestHeader:
    """Mark a parameter as a request header."""
    
    def __init__(self, name: Optional[str] = None, required: bool = True, default: Any = None):
        self.name = name
        self.required = required
        self.default = default


# ---- REST Controller Registry ----

class RestControllerRegistry:
    """Registry for REST controllers."""
    
    def __init__(self):
        self._controllers: Dict[str, Dict[str, Any]] = {}
    
    def register(self, controller_class: Type, path: str = "") -> None:
        """Register a REST controller."""
        self._controllers[controller_class.__name__] = {
            "class": controller_class,
            "path": path,
            "methods": self._extract_methods(controller_class),
        }
    
    def _extract_methods(self, controller_class: Type) -> Dict[str, Dict[str, Any]]:
        """Extract methods from a controller."""
        methods = {}
        for name, method in inspect.getmembers(controller_class, inspect.isfunction):
            if hasattr(method, '_spring_mapping'):
                methods[name] = {
                    "method": method,
                    "mapping": getattr(method, '_spring_mapping'),
                }
        return methods
    
    def get_controllers(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered controllers."""
        return self._controllers


class RestControllerRegistrar:
    """Register REST controllers with Flaxon routes."""
    
    def __init__(self, context: Any, registry: RestControllerRegistry, app: Any):
        self.context = context
        self.registry = registry
        self.app = app
    
    def register(self) -> None:
        """Register all REST controllers with Flaxon."""
        for name, controller_info in self.registry.get_controllers().items():
            self._register_controller(controller_info)
    
    def _register_controller(self, controller_info: Dict[str, Any]) -> None:
        """Register a single controller."""
        controller_class = controller_info["class"]
        base_path = controller_info["path"]
        
        # Create controller instance
        controller = self.context.get_bean(
            getattr(controller_class, "_spring_component_name", controller_class.__name__.lower()),
            controller_class,
        )
        
        for method_name, method_info in controller_info["methods"].items():
            method = method_info["method"]
            mapping = method_info["mapping"]
            
            path = self._join_paths(base_path, mapping.path)
            http_method = (mapping.method or "GET").lower()
            
            # Register route
            route_func = self._create_route_handler(controller, method, path)
            # Flaxon's router uses <name> path parameters, not the Spring-style
            # {name} syntax used throughout this plugin's own path templates.
            flaxon_path = self._to_flaxon_path(path)
            
            if http_method == "get":
                self.app.get(flaxon_path)(route_func)
            elif http_method == "post":
                self.app.post(flaxon_path)(route_func)
            elif http_method == "put":
                self.app.put(flaxon_path)(route_func)
            elif http_method == "delete":
                self.app.delete(flaxon_path)(route_func)
            elif http_method == "patch":
                self.app.patch(flaxon_path)(route_func)

    @staticmethod
    def _to_flaxon_path(path: str) -> str:
        """Convert a Spring-style {name} path template to Flaxon's <name> syntax."""
        return re.sub(r"\{(\w+)\}", r"<\1>", path)
    
    def _create_route_handler(self, controller: Any, method: Callable, path: str) -> Callable:
        """Create a route handler from a controller method."""
        from flaxon.http import Request
        
        async def handler(request: Request, **kwargs):
            # Resolve method parameters
            args = []
            sig = inspect.signature(method)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                annotation = param.annotation
                if annotation is inspect.Parameter.empty:
                    annotation = param.default
                
                if param_name == 'request':
                    args.append(request)
                elif param_name in kwargs:
                    args.append(kwargs[param_name])
                elif annotation is RequestBody or isinstance(annotation, RequestBody):
                    value = request.json()
                    args.append(await value if inspect.isawaitable(value) else value)
                elif annotation is RequestParam or isinstance(annotation, RequestParam):
                    marker = annotation if isinstance(annotation, RequestParam) else RequestParam()
                    name = marker.name or param_name
                    value = request.query_params.get(name)
                    if value is None:
                        value = marker.default
                    if value is None and marker.required:
                        raise ValueError(f"Missing required request parameter '{name}'")
                    args.append(value)
                elif annotation is PathVariable or isinstance(annotation, PathVariable):
                    marker = annotation if isinstance(annotation, PathVariable) else PathVariable()
                    name = marker.name or param_name
                    value = kwargs.get(name)
                    if value is None and marker.required:
                        raise ValueError(f"Missing required path variable '{name}'")
                    args.append(value)
                elif annotation is RequestHeader or isinstance(annotation, RequestHeader):
                    marker = annotation if isinstance(annotation, RequestHeader) else RequestHeader()
                    name = marker.name or param_name
                    value = request.headers.get(name)
                    if value is None:
                        value = marker.default
                    if value is None and marker.required:
                        raise ValueError(f"Missing required request header '{name}'")
                    args.append(value)
                else:
                    # Try to get from path parameters
                    if param_name in kwargs:
                        args.append(kwargs[param_name])
            
            # Call the method
            result = method(controller, *args)
            return await result if inspect.isawaitable(result) else result
        
        # Flaxon resolves endpoint parameters via inspect.signature(), so a
        # bare **kwargs is invisible to it -- give the handler an explicit
        # signature listing "request" plus every path variable.
        path_var_names = re.findall(r"\{(\w+)\}", path)
        sig_params = [inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request)]
        for name in path_var_names:
            sig_params.append(inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str))
        handler.__signature__ = inspect.Signature(sig_params)
        
        return handler

    @staticmethod
    def _join_paths(base_path: str, route_path: str) -> str:
        base = (base_path or "").rstrip("/")
        route = (route_path or "").lstrip("/")
        joined = f"{base}/{route}" if base and route else base or f"/{route}"
        if not joined.startswith("/"):
            joined = "/" + joined
        return joined if joined != "" else "/"