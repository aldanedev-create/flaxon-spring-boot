"""Profile management for Spring Boot."""

from typing import List, Optional, Set, Any
from functools import wraps
import inspect


class ProfileManager:
    """Manage active profiles."""
    
    def __init__(self, active_profiles: Optional[List[str]] = None):
        self._active_profiles: Set[str] = set(active_profiles or ["default"])
        self._default_profile = "default"
    
    def set_active_profiles(self, profiles: List[str]) -> None:
        """Set active profiles."""
        self._active_profiles = set(profiles)
    
    def add_active_profile(self, profile: str) -> None:
        """Add an active profile."""
        self._active_profiles.add(profile)
    
    def remove_active_profile(self, profile: str) -> None:
        """Remove an active profile."""
        self._active_profiles.discard(profile)
    
    def get_active_profiles(self) -> List[str]:
        """Get active profiles."""
        return list(self._active_profiles)
    
    def is_profile_active(self, profiles: List[str]) -> bool:
        """Check if any of the profiles are active."""
        return any(p in self._active_profiles for p in profiles)
    
    def is_profile_inactive(self, profiles: List[str]) -> bool:
        """Check if none of the profiles are active."""
        return all(p not in self._active_profiles for p in profiles)


class Profile:
    """Profile annotation for conditional beans."""
    
    def __init__(self, *profiles: str):
        self.profiles = list(profiles)
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_profile', self.profiles)
        return target


class EnableProfiles:
    """Enable specific profiles."""
    
    def __init__(self, *profiles: str):
        self.profiles = list(profiles)
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_profiles', self.profiles)
        return cls


def _get_profile_manager(args: tuple, kwargs: dict) -> Any:
    """Find the manager used by a guard without requiring it on the function."""
    manager = kwargs.get("profile_manager")
    if manager is not None:
        return manager
    for value in args:
        if hasattr(value, "is_profile_active") and hasattr(
            value, "is_profile_inactive"
        ):
            return value
    return None


def _call_guarded(func: Any, args: tuple, kwargs: dict) -> Any:
    """Do not forward the decorator-only profile_manager keyword by default."""
    if "profile_manager" not in kwargs:
        return func(*args, **kwargs)

    try:
        parameters = inspect.signature(func).parameters.values()
        accepts_manager = any(
            parameter.name == "profile_manager"
            or parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        )
    except (TypeError, ValueError):
        accepts_manager = False

    if accepts_manager:
        return func(*args, **kwargs)

    forwarded_kwargs = dict(kwargs)
    forwarded_kwargs.pop("profile_manager", None)
    return func(*args, **forwarded_kwargs)


def profile_required(profiles: List[str]):
    """Decorator to require a profile."""
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                profile_manager = _get_profile_manager(args, kwargs)
                if profile_manager and not profile_manager.is_profile_active(profiles):
                    raise ValueError(f"Required profiles {profiles} not active")
                result = _call_guarded(func, args, kwargs)
                return await result
            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            profile_manager = _get_profile_manager(args, kwargs)
            if profile_manager and not profile_manager.is_profile_active(profiles):
                raise ValueError(f"Required profiles {profiles} not active")
            return _call_guarded(func, args, kwargs)
        return wrapper
    return decorator


def profile_excluded(profiles: List[str]):
    """Decorator to exclude a profile."""
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                profile_manager = _get_profile_manager(args, kwargs)
                if profile_manager and profile_manager.is_profile_active(profiles):
                    raise ValueError(f"Excluded profiles {profiles} are active")
                result = _call_guarded(func, args, kwargs)
                return await result
            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            profile_manager = _get_profile_manager(args, kwargs)
            if profile_manager and profile_manager.is_profile_active(profiles):
                raise ValueError(f"Excluded profiles {profiles} are active")
            return _call_guarded(func, args, kwargs)
        return wrapper
    return decorator