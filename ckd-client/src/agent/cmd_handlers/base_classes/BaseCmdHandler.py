from src.agent.cmd_handlers.AbstractCmdHandler import AbstractCmdHandler
from src.utils.Executor import Executor


class BaseCmdHandler(AbstractCmdHandler):
    executor = Executor()

    @classmethod
    async def exec_shell_command(cls, command, args=None):
        """
        Form and execute shell command

        :param command: command to execute
        :param args: additional arguments
        :return: command output
        """
        if args is not None and len(args) > 0:
            cmd = command + ' ' + ' '.join(args)
        else:
            cmd = command

        return await cls.executor.async_exec_shell_command(cmd)
