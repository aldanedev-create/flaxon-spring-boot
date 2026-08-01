"""AOP/Aspect support for Spring Boot."""

import inspect
import asyncio
from typing import Any, Callable, Dict, List, Optional, Type
from functools import wraps


class Aspect:
    """Aspect annotation."""
    
    def __init__(self, order: int = 0):
        self.order = order
    
    def __call__(self, cls: Type) -> Type:
        setattr(cls, '_spring_aspect', True)
        setattr(cls, '_spring_aspect_order', self.order)
        setattr(cls, '_spring_component', True)
        setattr(cls, '_spring_component_name', cls.__name__.lower())
        return cls


class Before:
    """Before advice annotation."""
    
    def __init__(self, pointcut: str):
        self.pointcut = pointcut
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_before', True)
        setattr(target, '_spring_before_pointcut', self.pointcut)
        return target


class After:
    """After advice annotation."""
    
    def __init__(self, pointcut: str):
        self.pointcut = pointcut
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_after', True)
        setattr(target, '_spring_after_pointcut', self.pointcut)
        return target


class Around:
    """Around advice annotation."""
    
    def __init__(self, pointcut: str):
        self.pointcut = pointcut
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_around', True)
        setattr(target, '_spring_around_pointcut', self.pointcut)
        return target


class AfterReturning:
    """After returning advice annotation."""
    
    def __init__(self, pointcut: str, returning: str = "result"):
        self.pointcut = pointcut
        self.returning = returning
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_after_returning', True)
        setattr(target, '_spring_after_returning_pointcut', self.pointcut)
        setattr(target, '_spring_after_returning_returning', self.returning)
        return target


class AfterThrowing:
    """After throwing advice annotation."""
    
    def __init__(self, pointcut: str, throwing: str = "error"):
        self.pointcut = pointcut
        self.throwing = throwing
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_after_throwing', True)
        setattr(target, '_spring_after_throwing_pointcut', self.pointcut)
        setattr(target, '_spring_after_throwing_throwing', self.throwing)
        return target


class Pointcut:
    """Pointcut annotation."""
    
    def __init__(self, expression: str):
        self.expression = expression
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_pointcut', True)
        setattr(target, '_spring_pointcut_expression', self.expression)
        return target


class EnableAspectJAutoProxy:
    """Enable AspectJ auto-proxy."""
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_aspectj_auto_proxy', True)
        return cls


class AspectRegistry:
    """Registry for aspects."""
    
    def __init__(self):
        self._aspects: List[Dict[str, Any]] = []
    
    def register(self, aspect_class: Type) -> None:
        """Register an aspect."""
        advice = self._extract_advice(aspect_class)
        self._aspects.append({
            "class": aspect_class,
            "advice": advice,
            "order": getattr(aspect_class, '_spring_aspect_order', 0),
        })
    
    def _extract_advice(self, aspect_class: Type) -> Dict[str, Any]:
        """Extract advice from an aspect class."""
        advice = {}
        for name, method in inspect.getmembers(aspect_class, inspect.isfunction):
            if hasattr(method, '_spring_before'):
                advice.setdefault('before', []).append(method)
            if hasattr(method, '_spring_after'):
                advice.setdefault('after', []).append(method)
            if hasattr(method, '_spring_around'):
                advice.setdefault('around', []).append(method)
            if hasattr(method, '_spring_after_returning'):
                advice.setdefault('after_returning', []).append(method)
            if hasattr(method, '_spring_after_throwing'):
                advice.setdefault('after_throwing', []).append(method)
        return advice
    
    def get_aspects(self) -> List[Dict[str, Any]]:
        """Get all aspects."""
        return sorted(self._aspects, key=lambda x: x['order'])


class AspectWeaver:
    """Weave aspects into beans."""
    
    def __init__(self, context: Any, registry: AspectRegistry):
        self.context = context
        self.registry = registry
    
    def weave(self) -> None:
        """Weave aspects into all beans."""
        for aspect_info in self.registry.get_aspects():
            self._weave_aspect(aspect_info)
    
    def _weave_aspect(self, aspect_info: Dict[str, Any]) -> None:
        """Weave a single aspect."""
        aspect_class = aspect_info["class"]
        advice = aspect_info["advice"]
        
        # Create aspect instance
        aspect = self.context.get_bean(aspect_class.__name__.lower(), aspect_class)
        
        # Apply advice to matching beans
        for bean_name in self.context.get_bean_names():
            bean = self.context.get_bean(bean_name)
            self._apply_advice_to_bean(bean, advice, aspect)
    
    def _apply_advice_to_bean(self, bean: Any, advice: Dict[str, Any], aspect: Any) -> None:
        """Apply advice to a bean."""
        for method_name, method in list(inspect.getmembers(bean, inspect.ismethod)):
            if not method_name.startswith('_'):
                # Do not weave the aspect into itself.
                if bean is aspect:
                    continue
                if 'before' in advice and any(
                    self._matches(item, method_name) for item in advice['before']
                ):
                    self._wrap_with_before(bean, method_name, advice['before'], aspect)
                if 'after' in advice and any(
                    self._matches(item, method_name) for item in advice['after']
                ):
                    self._wrap_with_after(bean, method_name, advice['after'], aspect)
                if 'around' in advice and any(
                    self._matches(item, method_name) for item in advice['around']
                ):
                    self._wrap_with_around(bean, method_name, advice['around'], aspect)

    @staticmethod
    def _matches(advice: Callable, method_name: str) -> bool:
        """Match a simple pointcut name or wildcard expression."""
        expression = (
            getattr(advice, '_spring_before_pointcut', None)
            or getattr(advice, '_spring_after_pointcut', None)
            or getattr(advice, '_spring_around_pointcut', None)
            or getattr(advice, '_spring_after_returning_pointcut', None)
            or getattr(advice, '_spring_after_throwing_pointcut', None)
        )
        if not expression or expression in ("*", "execution(* *(..))"):
            return True
        pattern = expression.split(".")[-1].replace("()", "").replace("*", "")
        return not pattern or pattern in method_name

    @staticmethod
    def _advice_is_async(advice_list: List[Callable]) -> bool:
        return any(inspect.iscoroutinefunction(advice) for advice in advice_list)

    @staticmethod
    def _run_sync(value: Any) -> Any:
        if inspect.isawaitable(value):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(value)
            raise RuntimeError(
                "Async advice cannot wrap a synchronous method while an event loop is running"
            )
        return value

    @classmethod
    def _call_advice_sync(
        cls, advice_list: List[Callable], aspect: Any, *args: Any, **kwargs: Any
    ) -> None:
        for advice in advice_list:
            result = advice(aspect, *args, **kwargs)
            cls._run_sync(result)
    
    def _wrap_with_before(self, bean: Any, method_name: str, advice: Callable, aspect: Any) -> None:
        """Wrap a method with before advice."""
        original = getattr(bean, method_name)
        
        if not any(self._matches(item, method_name) for item in advice):
            return
        if inspect.iscoroutinefunction(original) or self._advice_is_async(advice):
            @wraps(original)
            async def wrapped(*args, **kwargs):
                for item in advice:
                    if self._matches(item, method_name):
                        result = item(aspect, *args, **kwargs)
                        if inspect.isawaitable(result):
                            await result
                result = original(*args, **kwargs)
                return await result if inspect.isawaitable(result) else result
        else:
            @wraps(original)
            def wrapped(*args, **kwargs):
                self._call_advice_sync(advice, aspect, *args, **kwargs)
                return original(*args, **kwargs)
        
        setattr(bean, method_name, wrapped)
    
    def _wrap_with_after(self, bean: Any, method_name: str, advice: Callable, aspect: Any) -> None:
        """Wrap a method with after advice."""
        original = getattr(bean, method_name)
        
        if not any(self._matches(item, method_name) for item in advice):
            return
        if inspect.iscoroutinefunction(original) or self._advice_is_async(advice):
            @wraps(original)
            async def wrapped(*args, **kwargs):
                try:
                    result = original(*args, **kwargs)
                    result = await result if inspect.isawaitable(result) else result
                    for item in advice:
                        if self._matches(item, method_name):
                            value = item(aspect, *args, **kwargs)
                            if inspect.isawaitable(value):
                                await value
                    return result
                except Exception as error:
                    for item in advice:
                        if self._matches(item, method_name):
                            value = item(aspect, *args, **kwargs, error=error)
                            if inspect.isawaitable(value):
                                await value
                    raise
        else:
            @wraps(original)
            def wrapped(*args, **kwargs):
                try:
                    result = original(*args, **kwargs)
                    self._call_advice_sync(advice, aspect, *args, **kwargs)
                    return result
                except Exception as error:
                    for item in advice:
                        if self._matches(item, method_name):
                            self._run_sync(item(aspect, *args, **kwargs, error=error))
                    raise
        
        setattr(bean, method_name, wrapped)
    
    def _wrap_with_around(self, bean: Any, method_name: str, advice: Callable, aspect: Any) -> None:
        """Wrap a method with around advice."""
        original = getattr(bean, method_name)
        
        if not any(self._matches(item, method_name) for item in advice):
            return

        class ProceedingJoinPoint:
            def __init__(self, method, args, kwargs):
                self.method = method
                self.args = args
                self.kwargs = kwargs

            async def proceed(self):
                result = self.method(*self.args, **self.kwargs)
                return await result if inspect.isawaitable(result) else result

            def proceed_sync(self):
                return self.method(*self.args, **self.kwargs)

        if inspect.iscoroutinefunction(original) or self._advice_is_async(advice):
            @wraps(original)
            async def wrapped(*args, **kwargs):
                join_point = ProceedingJoinPoint(original, args, kwargs)
                selected = next(
                    item for item in advice if self._matches(item, method_name)
                )
                value = selected(aspect, join_point, *args, **kwargs)
                return await value if inspect.isawaitable(value) else value
        else:
            @wraps(original)
            def wrapped(*args, **kwargs):
                join_point = ProceedingJoinPoint(original, args, kwargs)
                selected = next(
                    item for item in advice if self._matches(item, method_name)
                )
                value = selected(aspect, join_point, *args, **kwargs)
                return self._run_sync(value)
        
        setattr(bean, method_name, wrapped)