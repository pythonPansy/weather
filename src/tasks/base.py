import abc

class BaseTask(abc.ABC):
    @abc.abstractmethod
    def run(self, config: dict) -> dict:
        pass