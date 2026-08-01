"""Scheduled task support for Spring Boot."""

import asyncio
import inspect
import threading
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta

try:
    from croniter import croniter
except ImportError:  # Keep the package importable when croniter is optional.
    croniter = None


class Scheduled:
    """Scheduled task annotation."""
    
    def __init__(
        self,
        cron: Optional[str] = None,
        fixed_delay: Optional[int] = None,
        fixed_rate: Optional[int] = None,
        initial_delay: Optional[int] = None,
    ):
        self.cron = cron
        self.fixed_delay = fixed_delay
        self.fixed_rate = fixed_rate
        self.initial_delay = initial_delay
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_scheduled', True)
        setattr(target, '_spring_scheduled_cron', self.cron)
        setattr(target, '_spring_scheduled_fixed_delay', self.fixed_delay)
        setattr(target, '_spring_scheduled_fixed_rate', self.fixed_rate)
        setattr(target, '_spring_scheduled_initial_delay', self.initial_delay)
        return target


class EnableScheduling:
    """Enable scheduling."""
    
    def __call__(self, cls: Any) -> Any:
        setattr(cls, '_spring_enable_scheduling', True)
        return cls


class ScheduledTaskRunner:
    """Run scheduled tasks."""
    
    def __init__(self):
        self._tasks: List[Dict[str, Any]] = []
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[threading.Thread] = None
    
    def register(self, task: Callable, config: Dict[str, Any]) -> None:
        """Register a scheduled task."""
        self._tasks.append({
            "task": task,
            "config": config,
            "last_run": None,
            "next_run": None,
        })
    
    def start(self) -> None:
        """Start running scheduled tasks."""
        if self._running:
            return
        
        self._running = True
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._thread = threading.Thread(
                target=lambda: asyncio.run(self._run_loop()),
                name="flaxon-scheduled-tasks",
                daemon=True,
            )
            self._thread.start()
        else:
            self._task = loop.create_task(self._run_loop())
    
    def stop(self) -> None:
        """Stop running scheduled tasks."""
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def _run_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            now = datetime.now()
            
            for task_info in self._tasks:
                await self._run_task_if_due(task_info, now)
            
            # Wait before checking again
            await asyncio.sleep(1)
    
    async def _run_task_if_due(self, task_info: Dict[str, Any], now: datetime) -> None:
        """Run a task if it's due."""
        config = task_info["config"]
        
        if config.get("cron"):
            cron = config["cron"]
            if croniter is None:
                raise RuntimeError(
                    "croniter is required for cron-based scheduled tasks"
                )
            if croniter.is_valid(cron):
                if task_info["next_run"] is None:
                    task_info["next_run"] = croniter(cron, now).get_next(datetime)
                
                if now >= task_info["next_run"]:
                    await self._execute_task(task_info)
                    task_info["next_run"] = croniter(cron, now).get_next(datetime)
        
        elif config.get("fixed_delay"):
            delay = config["fixed_delay"]
            if task_info["last_run"] is None or (now - task_info["last_run"]).total_seconds() >= delay / 1000:
                await self._execute_task(task_info)
                task_info["last_run"] = now
        
        elif config.get("fixed_rate"):
            rate = config["fixed_rate"]
            if task_info["last_run"] is None or (now - task_info["last_run"]).total_seconds() >= rate / 1000:
                await self._execute_task(task_info)
                task_info["last_run"] = now
    
    async def _execute_task(self, task_info: Dict[str, Any]) -> None:
        """Execute a scheduled task."""
        try:
            task = task_info["task"]
            if inspect.iscoroutinefunction(task):
                await task()
            else:
                task()
        except Exception as e:
            print(f"Scheduled task error: {e}", flush=True)


class ScheduledTaskInitializer:
    """Initialize scheduled tasks from beans."""
    
    def __init__(self, context: Any, runner: ScheduledTaskRunner, app: Any):
        self.context = context
        self.runner = runner
        self.app = app
    
    def initialize(self) -> None:
        """Initialize scheduled tasks."""
        # Find all beans with scheduled methods
        for bean_name in self.context.get_bean_names():
            bean = self.context.get_bean(bean_name)
            self._scan_bean(bean)
    
    def _scan_bean(self, bean: Any) -> None:
        """Scan a bean for scheduled methods."""
        for name, method in inspect.getmembers(bean, inspect.ismethod):
            if hasattr(method, '_spring_scheduled'):
                config = {
                    "cron": getattr(method, '_spring_scheduled_cron', None),
                    "fixed_delay": getattr(method, '_spring_scheduled_fixed_delay', None),
                    "fixed_rate": getattr(method, '_spring_scheduled_fixed_rate', None),
                    "initial_delay": getattr(method, '_spring_scheduled_initial_delay', None),
                }
                self.runner.register(method, config)