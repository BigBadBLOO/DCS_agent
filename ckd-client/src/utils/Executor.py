import asyncio
import subprocess as subp

from src.utils.Exceptions import ShellExecutionError
from src.utils.Singleton import Singleton


class Executor(metaclass=Singleton):
    __separator = ' && '

    @classmethod
    def wrap_async_call(cls, func, *args):
        """
        Asynchronously execute function in asyncio loop

        :param func: function to execute
        :param args: arguments of the desired func execution
        :return: result of the func(args) expression
        """
        loop = cls.__get_current_async_loop()
        res = loop.run_until_complete(func(*args))
        return res

    @staticmethod
    def __get_current_async_loop():
        """
        Support function for getting current asyncio event loop

        :return: current asyncio event loop
        """
        try:
            cur_loop = asyncio.get_event_loop()
        except RuntimeError:
            cur_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cur_loop)
        return cur_loop

    @classmethod
    async def async_execution(cls, func, *args):
        """
        Function to make sync functions execute asynchronously

        :param func: callable that requires asynchronous execution
        :param args: arguments to pass
        :return: the result of the func(args) async execution
        """
        loop = cls.__get_current_async_loop()
        return await loop.run_in_executor(None, func, *args)

    @classmethod
    async def async_exec_cmds_with_wrapping(cls, commands: list, dir_to_use: str):
        new_commands = ['pushd {}'.format(dir_to_use)]

        for cmd in commands:
            new_commands.append(cmd)

        new_commands.append('popd')
        return await cls.async_exec_commands_in_one_shell(new_commands, cls.__separator)

    @classmethod
    async def async_exec_commands_in_one_shell(cls, commands: list, separator: str):
        return await cls.async_exec_shell_command(separator.join(commands))

    @staticmethod
    def execute_shell_command(cmd: str) -> str:
        """
        Make OS execute command

        :param cmd: shell command to execute
        :return: shell command output
        """
        res = subp.getstatusoutput(cmd)
        if res[0] != 0:
            raise ShellExecutionError(cmd, res[0], res[1])
        return res[1]

    @classmethod
    async def async_exec_shell_command(cls, cmd: str):
        """
        Asynchronously execute shell command

        :param cmd: shell command to execute
        :return: execution result
        """
        return await cls.async_execution(cls.execute_shell_command, cmd)
