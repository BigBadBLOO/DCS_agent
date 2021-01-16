import os
from multiprocessing import Queue

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.AbstractCmdHandler import AbstractCmdHandler
from src.agent.cmd_handlers.impls.HPCStatsCmdHandler import HPCStatsCmdHandler
from src.agent.cmd_handlers.impls.StatsCmdHandler import StatsCmdHandler
from src.agent.compilation_handling.CompilationHandler import CompilationHandler
from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import Command, TaskStatus
from src.utils.Exceptions import CmdHandlerError
from src.utils.Executor import Executor
from src.utils.data_types.Task import Task
from src.utils.io.IOHandler import IOHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class RunCmdHandler(AbstractCmdHandler):

    def __init__(self, streams_handler: StreamsHandler, template_resolver: TemplateResolver, io_handler: IOHandler,
                 logger_queue: Queue, workdir: str, server_addr: str):

        # for writing files
        self.__io_handler = io_handler

        # for receiving/sending data to the web application using sockets
        self.__streams_handler = streams_handler

        self.__executor = Executor()

        # support classes
        self.__template_resolver = template_resolver
        self.__compilation_handler = CompilationHandler(template_resolver, logger_queue, workdir)

        self.__task_stats_handler = StatsCmdHandler(streams_handler, template_resolver, io_handler, logger_queue)
        self.__hpc_stats_handler = HPCStatsCmdHandler(
            template_resolver=template_resolver,
            hpc_stats_resolver=HPCStatsResolver(template_resolver.get_templ_sign(), logger_queue),
            logger_queue=logger_queue,
            server_addr=server_addr
        )

        self.__workdir = workdir

        self.__log_writer = NamedLogWriter(logger_queue, 'RunCmdHandler')

        super().__init__()

    async def handle(self, task: Task, args: list):
        """
        Method for handling compilation and scheduling of the incoming task
        :param task: incoming task
        :param args: additional arguments for compilation
        :raises CmdHandlerError
        :return: nothing
        """
        self.__set_task_log(task)

        task = await self.__streams_handler.recv_file(task)

        task.set_status(TaskStatus.COMPILING)
        await self.__io_handler.save_task(task)
        await self.__streams_handler.inform_client(task, 'Task is compiling')

        try:
            await self.__compilation_handler.handle_compilation(task, args)
            if self.__template_resolver.sched_uses_desc():
                await self.__create_task_passport(task)
            await self.__run_task(task)

            # Update HPC info on the web application side
            await self.__hpc_stats_handler.handle(task, [])
        except Exception as e:
            raise CmdHandlerError(Command.RUN, e)

    async def __create_task_passport(self, task):
        passport = self.__template_resolver.get_passport(task)
        passport_name = await self.__io_handler.write_task_passport(task, passport)
        task.set_passport_name(passport_name)

    async def __run_task(self, task):
        """
        Handle 'run' command: compile source files into binary and schedule its execution

        :param task: related task
        :raises ShellExecutionError
        :return: None
        """
        run_command = self.__template_resolver.get_run_for_task(task)

        res = await self.__executor.async_exec_cmds_with_wrapping(
            commands=[run_command],
            dir_to_use=task.get_dir_name_for_task(self.__workdir),
        )

        self.__update_jobid(res, task)

        await self.__io_handler.save_task(task)

        return None

    def __set_task_log(self, task):
        """
        Set full path to log for the incoming task

        :param task: relevant task
        :return: nothing
        """
        log_name = os.path.join(
            task.get_dir_name_for_task(self.__workdir),
            '{}.log'.format(task.get_name())
        )
        task.set_log_name(log_name)

    def __update_jobid(self, res, task):
        """
        Updates jobid depending on the command output

        :param res: 'run' command output
        :param task: related task
        :raises MissingTemplateElement
        :return: nothing
        """
        jobid = self.__template_resolver.resolve_jobid_from_output(res)

        task.set_jobid(jobid)
        self.__log_writer.log('Job Id for task {} is {}'.format(task.get_name(), task.get_jobid()))
