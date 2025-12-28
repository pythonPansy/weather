from typing import Type
from base import BaseTask

TASK_REGISTRY: dict[str, Type[BaseTask]] = {}


def register_task(name: str):
    """Register a task class under `name`. Raises ValueError on duplicate names."""
    def decorator(task_cls: Type[BaseTask]) -> Type[BaseTask]:
        if name in TASK_REGISTRY:
            raise ValueError(f"Task name '{name}' is already registered for {TASK_REGISTRY[name].__name__}")
        TASK_REGISTRY[name] = task_cls
        return task_cls
    return decorator



