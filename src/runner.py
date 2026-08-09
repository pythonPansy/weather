import yaml

import src.tasks  # noqa: F401 — register tasks via side-effect imports

from .config_env import expand_env_vars
from .context import PipelineContext
from .logging_config import get_logger
from .tasks.registry import TASK_REGISTRY

logger = get_logger(__name__)


class TaskRunner:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = expand_env_vars(yaml.safe_load(f))

    def run(self) -> PipelineContext:
        context = PipelineContext()

        for task_cfg in self.config["tasks"]:
            task_type = task_cfg["type"]
            params = task_cfg.get("params", {})

            logger.info("Running task %s", task_type)
            task_cls = TASK_REGISTRY[task_type]
            task = task_cls(params)

            context = task.run(context)
            logger.info("Finished task %s", task_type)

        return context
