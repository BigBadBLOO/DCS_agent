from src.utils.Exceptions import NotOverriddenError
from src.utils.data_types.Task import Task


class AbstractCmdHandler:

    async def handle(self, task: Task, args: list):
        """
        Main handling method. Must be overridden in the AbstractCmdHandler's subclasses that do actual command handling.

        :param task: task to handle
        :param args: additional arguments
        :return: updated task
        """
        raise NotOverriddenError()
