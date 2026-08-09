import abc

from src.context import PipelineContext


class BaseTask(abc.ABC):
    @abc.abstractmethod
    def run(self, context: PipelineContext) -> PipelineContext:
        pass
