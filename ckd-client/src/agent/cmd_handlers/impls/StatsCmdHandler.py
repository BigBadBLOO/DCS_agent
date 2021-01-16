from multiprocessing import Queue

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.base_classes.BaseCmdHandler import BaseCmdHandler
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import LogLevel, TaskStatus, Command
from src.utils.Exceptions import CmdHandlerError
from src.utils.data_types.Task import Task
from src.utils.io.IOHandler import IOHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class StatsCmdHandler(BaseCmdHandler):

    def __init__(self, streams_handler: StreamsHandler, template_resolver: TemplateResolver, io_handler: IOHandler,
                 logger_queue: Queue):
        self.__streams_handler = streams_handler
        self.__template_resolver = template_resolver
        self.__log_writer = NamedLogWriter(logger_queue, 'StatsCmdHandler')
        self.__io_handler = io_handler

    async def handle(self, task: Task, args: list):
        task = await self.__io_handler.restore_task(task)
        error = task.get_error()

        if error is not None and error != 'None':
            task.set_status(TaskStatus.ERROR)
            msg = 'Error:'
        else:
            task = await self.__get_stats_for_task(task, args)
            msg = 'Task is currently {}'.format(task.get_str_status())

        await self.__streams_handler.inform_client(task, msg, error)

    async def __get_stats_for_task(self, task: Task, args: list) -> Task:
        """
        Handle 'stats' command

        :param task: related task
        :param args: additional arguments
        :return: None
        """
        stats_command = self.__template_resolver.get_stats_for_task(task)
        sched = self.__template_resolver.get_sched()
        try:
            res = await self.exec_shell_command(stats_command, args)
            res = res.split('\n')
            res = list(filter(lambda x: task.get_jobid() in x, res))
            if len(res) == 0:
                raise CmdHandlerError(Command.STATS, 'Unknown task: {}'.format(task.get_name()))

            res = list(filter(lambda x: sched.is_status(x), res[0].split(' ')))
            if len(res) == 0:
                raise CmdHandlerError(Command.STATS, 'Unknown status for task: {}'.format(task.get_name()))

            task.set_status(TaskStatus(sched.get_task_status(res[0])))
            self.__log_writer.log('Task\'s status is: {}'.format(task.get_status()), level=LogLevel.DEBUG)

        except Exception as e:
            if task.get_status() == TaskStatus.COMPILING:
                pass
            elif 'Mr. Tester' in sched.get_name():
                task.set_status(TaskStatus.CANCELLED)
            else:
                raise e

        return task
