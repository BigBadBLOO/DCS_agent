from multiprocessing import Queue

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.base_classes.BaseCmdHandler import BaseCmdHandler
from src.agent.cmd_handlers.impls.HPCStatsCmdHandler import HPCStatsCmdHandler
from src.agent.cmd_handlers.impls.StatsCmdHandler import StatsCmdHandler
from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import TaskStatus
from src.utils.data_types.Task import Task
from src.utils.io.IOHandler import IOHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class CancelCmdHandler(BaseCmdHandler):

    def __init__(self, streams_handler: StreamsHandler, template_resolver: TemplateResolver, io_handler: IOHandler,
                 logger_queue: Queue, server_addr):
        self.__streams_handler = streams_handler
        self.__template_resolver = template_resolver
        self.__io_handler = io_handler
        self.__server_addr = server_addr
        self.__task_stats_handler = StatsCmdHandler(streams_handler, template_resolver, io_handler, logger_queue)
        self.__hpc_stats_handler = HPCStatsCmdHandler(
            template_resolver=template_resolver,
            hpc_stats_resolver=HPCStatsResolver(template_resolver.get_templ_sign(), logger_queue),
            logger_queue=logger_queue,
            server_addr=server_addr
        )

        self.__log_writer = NamedLogWriter(logger_queue, 'CancelCmdHandler')

    async def handle(self, task: Task, args: list):
        task = await self.__io_handler.restore_task(task)
        await self.__cancel_task(task, args)
        await self.__io_handler.save_task(task)

        # Update task's status
        await self.__task_stats_handler.handle(task, [])

        # Update HPC info on the web application side
        await self.__hpc_stats_handler.handle(task, [])

    async def __cancel_task(self, task: Task, args: list):
        """
        Handle 'cancel' command

        :param task: related task
        :param args: additional arguments
        :return: None
        """
        cancel_command = self.__template_resolver.get_cancel_for_task(task)
        await self.exec_shell_command(cancel_command, args)
        task.set_status(TaskStatus.CANCELLED)

        return None
