import abc

from ..context import PipelineContext


class BaseTask(abc.ABC):
    @abc.abstractmethod
    def run(self, context: PipelineContext) -> PipelineContext:
        pass
