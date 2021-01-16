from asyncio import StreamReader, StreamWriter
from multiprocessing import Queue
from multiprocessing.connection import Connection

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.CmdHandlerFactory import CmdHandlerFactory
from src.agent.template_handling.TemplateResolver import TemplateResolver, TemplateResolverBuilder
from src.utils.Enums import LogLevel, TaskStatus
from src.utils.SchedsDownloader import SchedsDownloader
from src.utils.data_types.Task import Task
from src.utils.io.IOHandler import IOHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class RequestHandler:
    HANDLER_ERROR = 'Handler Error:'

    def __init__(self, template_resolver: TemplateResolver, workdir: str, logger_queue: Queue,
                 writing_end_of_pipe: Connection):
        self.__workdir = workdir

        self.__writing_conn = writing_end_of_pipe
        self.__sources = set()

        self.__template_resolver = template_resolver
        self.__log_writer = NamedLogWriter(logger_queue, 'RequestHandler')
        self.__io_handler = IOHandler(self.__workdir, logger_queue)
        self.__logger_queue = logger_queue

        self.__cmd_handler_factory = CmdHandlerFactory()

    async def __handle(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Method for async handling incoming request

        :param reader: async reader channel
        :param writer: async writer channel
        :return: nothing
        """

        task = None  # type: Task
        self.__log_writer.log('Async Handling connection', level=LogLevel.DEBUG)
        streams_handler = StreamsHandler(reader, writer, self.__io_handler, self.__logger_queue)
        try:
            source, cmd, task, args = await streams_handler.parse_incoming_data()

            task_desc = task.to_json(indent=4) if task is not None else 'Empty task'
            self.__log_writer.log(
                'Incoming request:\nsource:\t{}\ncmd:\t{}\ntask:\n{}\nargs:\t{}'.format(source, cmd, task_desc, args),
                level=LogLevel.DEBUG
            )

            if self.__template_resolver is None and self.__sources == set():
                self.__template_resolver = self.__create_template_resolver(source)
                self.__send_scheduler_info_through_conn()

            if source is not None and source != 'None':
                if source not in self.__sources:
                    self.__writing_conn.send(source)

                self.__log_writer.log('Web application address: {}'.format(source))
                self.__sources.add(source)

            cmd_handler = self.__cmd_handler_factory.get_handler(cmd, streams_handler, self.__template_resolver,
                                                                 self.__logger_queue, source, self.__workdir)

            args = self.__parse_args(args)
            await cmd_handler.handle(task, args)

        except ValueError as ve:
            await streams_handler.inform_client(
                task,
                self.HANDLER_ERROR,
                RuntimeError('{}. Supported commands: {}'.format(ve, self.__get_supported_cmds())),
            )

        except Exception as e:
            if task is not None and task.exists(self.__workdir):
                task.set_status(TaskStatus.ERROR)
                task.set_error(e)
                await self.__io_handler.save_task(task)
                self.__log_writer.log(task.to_json(indent=4), level=LogLevel.ERROR)
            await streams_handler.inform_client(task, self.HANDLER_ERROR, e)

    def __create_template_resolver(self, source):
        downloader = SchedsDownloader(source)
        scheds_list = downloader.get_scheds_from_db()
        return TemplateResolverBuilder.build(self.__workdir, scheds_list, self.__logger_queue)

    def __send_scheduler_info_through_conn(self):
        sched = self.__template_resolver.get_sched()
        self.__writing_conn.send(self.__workdir)
        self.__writing_conn.send(sched.to_json())

    async def safe_handle(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Method for async handling incoming request that doesn't raise Exceptions

        :param reader: async reader channel
        :param writer: async writer channel
        :return: nothing
        """
        try:
            await self.__handle(reader, writer)
        except Exception as e:
            self.__log_writer.log('Safe handle fallback: {}'.format(e), level=LogLevel.ERROR)

    @staticmethod
    def __parse_args(in_args: str) -> list:
        """
        Convert arguments string to list

        :param in_args: arguments string
        :return: arguments as a list of strings
        """
        args = []
        if isinstance(in_args, type('str')) and len(in_args) > 0:
            args = in_args.split(' ')
        # if still string then there was only one elem ==> turn it into list
        if isinstance(args, type('str')) and args != '':
            args = [args]
        return args

    def __get_supported_cmds(self):
        return list(
            map(
                lambda x: x.value,
                self.__cmd_handler_factory.get_supported_commands()
            )
        )
