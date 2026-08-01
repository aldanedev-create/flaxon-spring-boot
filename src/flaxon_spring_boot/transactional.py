"""Transactional support for Spring Boot."""

import asyncio
import inspect
from typing import Any, Callable, Optional, Type
from functools import wraps


class Transactional:
    """Transaction annotation."""
    
    def __init__(
        self,
        propagation: str = "REQUIRED",
        isolation: str = "DEFAULT",
        timeout: Optional[int] = None,
        read_only: bool = False,
        rollback_for: Optional[list] = None,
        no_rollback_for: Optional[list] = None,
    ):
        self.propagation = propagation
        self.isolation = isolation
        self.timeout = timeout
        self.read_only = read_only
        self.rollback_for = rollback_for or []
        self.no_rollback_for = no_rollback_for or []
    
    def __call__(self, target: Any) -> Any:
        setattr(target, '_spring_transactional', True)
        setattr(target, '_spring_transactional_propagation', self.propagation)
        setattr(target, '_spring_transactional_isolation', self.isolation)
        setattr(target, '_spring_transactional_timeout', self.timeout)
        setattr(target, '_spring_transactional_read_only', self.read_only)
        setattr(target, '_spring_transactional_rollback_for', self.rollback_for)
        setattr(target, '_spring_transactional_no_rollback_for', self.no_rollback_for)
        return target


class TransactionManager:
    """Transaction manager."""
    
    def __init__(self, context: Any):
        self.context = context
        self._transaction_stack: list = []
    
    async def execute_in_transaction(self, func: Callable, config: dict) -> Any:
        """Execute a function in a transaction."""
        # Get transaction manager from context
        try:
            tx_manager = self.context.get_bean('transaction_manager')
        except (ValueError, KeyError):
            tx_manager = None
        if tx_manager is None:
            result = func()
            return await result if inspect.isawaitable(result) else result
        
        try:
            # Begin transaction
            if hasattr(tx_manager, 'begin'):
                result = tx_manager.begin()
                if inspect.isawaitable(result):
                    await result
            
            # Execute function
            result = func()
            if inspect.isawaitable(result):
                result = await result
            
            # Commit transaction
            if hasattr(tx_manager, 'commit'):
                commit_result = tx_manager.commit()
                if inspect.isawaitable(commit_result):
                    await commit_result
            
            return result
        
        except Exception as e:
            # Rollback on exception
            if hasattr(tx_manager, 'rollback'):
                rollback_result = tx_manager.rollback()
                if inspect.isawaitable(rollback_result):
                    await rollback_result
            
            # Check if exception should be rolled back
            rollback_for = config.get('rollback_for', [])
            no_rollback_for = config.get('no_rollback_for', [])
            
            should_rollback = True
            for no_rollback_type in no_rollback_for:
                if isinstance(e, no_rollback_type):
                    should_rollback = False
                    break
            
            if should_rollback:
                for rollback_type in rollback_for:
                    if isinstance(e, rollback_type):
                        should_rollback = True
                        break
            
            if should_rollback:
                raise e
            else:
                return None
    
    def is_transaction_active(self) -> bool:
        """Check if a transaction is active."""
        return len(self._transaction_stack) > 0


def transactional(func: Callable) -> Callable:
    """Decorator for transactional methods."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get transaction manager from context
        # This would be injected via DI
        if hasattr(func, '_spring_transactional'):
            config = {
                'propagation': getattr(func, '_spring_transactional_propagation', 'REQUIRED'),
                'isolation': getattr(func, '_spring_transactional_isolation', 'DEFAULT'),
                'timeout': getattr(func, '_spring_transactional_timeout', None),
                'read_only': getattr(func, '_spring_transactional_read_only', False),
                'rollback_for': getattr(func, '_spring_transactional_rollback_for', []),
                'no_rollback_for': getattr(func, '_spring_transactional_no_rollback_for', []),
            }
            # Execute in transaction
            # This would use the TransactionManager
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return result
            return result
        return func(*args, **kwargs)
    return wrapper