"""Event support for Spring Boot."""

import asyncio
import inspect
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from functools import wraps


class Event:
    """Base event class."""
    
    def __init__(self, source: Any = None):
        self.source = source
        self.timestamp = datetime.now()


class EventListener:
    """Event listener annotation."""
    
    def __init__(self, event_type: Optional[Type] = None, condition: str = ""):
        self.event_type = event_type
        self.condition = condition
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_event_listener', True)
        setattr(target, '_spring_event_listener_type', self.event_type)
        setattr(target, '_spring_event_listener_condition', self.condition)
        return target


class EnableAsync:
    """Enable async event processing."""
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_async', True)
        return cls


class ApplicationEventPublisher:
    """Event publisher."""
    
    def __init__(self):
        self._listeners: Dict[Type, List[Callable]] = {}
        self._async_listeners: List[Callable] = []
        self._sync_listeners: List[Callable] = []
    
    def register_listener(self, event_type: Type, listener: Callable, async_mode: bool = False) -> None:
        """Register an event listener."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        
        if async_mode:
            self._async_listeners.append(listener)
        else:
            self._sync_listeners.append(listener)
    
    def publish_event(self, event: Any) -> None:
        """Publish an event."""
        event_type = type(event)
        
        listeners = list(self._listeners.get(event_type, []))
        # Also notify listeners registered for a base event type.
        for registered_type, registered_listeners in self._listeners.items():
            if registered_type is not event_type and isinstance(event, registered_type):
                listeners.extend(registered_listeners)

        for listener in listeners:
            if listener in self._async_listeners:
                self._schedule_async(self._run_async_listener(listener, event))
            else:
                # Run sync listener
                self._run_sync_listener(listener, event)

    @staticmethod
    def _schedule_async(coroutine: Any) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # A publisher is often called from synchronous application startup.
            # Run the coroutine to completion instead of calling create_task()
            # without a running event loop.
            asyncio.run(coroutine)
        else:
            loop.create_task(coroutine)
    
    async def _run_async_listener(self, listener: Callable, event: Any) -> None:
        """Run an async listener."""
        try:
            result = listener(event)
            if inspect.isawaitable(result):
                await result
        except Exception:
            pass
    
    def _run_sync_listener(self, listener: Callable, event: Any) -> None:
        """Run a sync listener."""
        try:
            listener(event)
        except Exception:
            pass


class EventPublisher:
    """Event publisher for Spring Boot."""
    
    def __init__(self):
        self.processor: Optional[Any] = None
        self._publisher = ApplicationEventPublisher()
    
    def register_listener(self, event_type: Type, listener: Callable) -> None:
        """Register an event listener."""
        async_mode = hasattr(listener, '_spring_async')
        self._publisher.register_listener(event_type, listener, async_mode)
    
    def publish_event(self, event: Any) -> None:
        """Publish an event."""
        self._publisher.publish_event(event)
    
    def get_publisher(self) -> ApplicationEventPublisher:
        """Get the underlying publisher."""
        return self._publisher


class AsyncEventProcessor:
    """Async event processor."""
    
    def __init__(self, context: Any):
        self.context = context
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task = None
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start the async event processor."""
        self._running = True
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._thread = threading.Thread(
                target=lambda: asyncio.run(self._process_loop()),
                name="flaxon-async-events",
                daemon=True,
            )
            self._thread.start()
        else:
            self._task = loop.create_task(self._process_loop())
    
    def stop(self) -> None:
        """Stop the async event processor."""
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def _process_loop(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await self._queue.get()
                await self._process_event(event)
            except asyncio.CancelledError:
                break
            except Exception:
                pass
    
    async def _process_event(self, event: Any) -> None:
        """Process a single event through the configured publisher."""
        publisher = getattr(self.context, "event_publisher", None)
        if publisher is not None:
            publisher.publish_event(event)


def async_event_listener(func: Callable) -> Callable:
    """Decorator for async event listeners."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    setattr(wrapper, '_spring_async', True)
    return wrapper