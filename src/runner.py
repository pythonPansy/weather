import yaml
from .tasks.registry import TASK_REGISTRY

class TaskRunner:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def run(self) -> dict:
        context: dict = {}

        for task_cfg in self.config["tasks"]:
            task_type = task_cfg["type"]
            params = task_cfg.get("params", {})

            task_cls = TASK_REGISTRY[task_type]
            task = task_cls(params)

            context = task.run(context)

        return context
