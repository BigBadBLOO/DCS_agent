from multiprocessing import Queue

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.AbstractCmdHandler import AbstractCmdHandler
from src.agent.cmd_handlers.impls.CancelCmdHandler import CancelCmdHandler
from src.agent.cmd_handlers.impls.HPCStatsCmdHandler import HPCStatsCmdHandler
from src.agent.cmd_handlers.impls.ResultsCmdHandler import ResultsCmdHandler
from src.agent.cmd_handlers.impls.RunCmdHandler import RunCmdHandler
from src.agent.cmd_handlers.impls.SourcesCmdHandler import SourcesCmdHandler
from src.agent.cmd_handlers.impls.StatsCmdHandler import StatsCmdHandler
from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import Command, MetaArg
from src.utils.Singleton import Singleton
from src.utils.io.IOHandler import IOHandler


class CmdHandlerFactory(metaclass=Singleton):
    __handlers = {
        Command.RUN:       RunCmdHandler,
        Command.STATS:     StatsCmdHandler,
        Command.CANCEL:    CancelCmdHandler,

        Command.HPC_STATS: HPCStatsCmdHandler,

        Command.SOURCES:   SourcesCmdHandler,
        Command.RESULTS:   ResultsCmdHandler,
    }

    __args = {
        Command.RUN:       (MetaArg.STREAMS_HANDLER, MetaArg.TEMPLATE_RESOLVER, MetaArg.IO_HANDLER,
                            MetaArg.LOGGER_QUEUE, MetaArg.WORKDIR, MetaArg.SERVER_ADDR),
        Command.STATS:     (MetaArg.STREAMS_HANDLER, MetaArg.TEMPLATE_RESOLVER, MetaArg.IO_HANDLER,
                            MetaArg.LOGGER_QUEUE),
        Command.CANCEL:    (MetaArg.STREAMS_HANDLER, MetaArg.TEMPLATE_RESOLVER, MetaArg.IO_HANDLER,
                            MetaArg.LOGGER_QUEUE, MetaArg.SERVER_ADDR),

        Command.HPC_STATS: (MetaArg.TEMPLATE_RESOLVER, MetaArg.HPCSTATS_RESOLVER, MetaArg.LOGGER_QUEUE,
                            MetaArg.SERVER_ADDR),

        Command.SOURCES:   (MetaArg.STREAMS_HANDLER, MetaArg.IO_HANDLER, MetaArg.LOGGER_QUEUE),
        Command.RESULTS:   (MetaArg.STREAMS_HANDLER, MetaArg.IO_HANDLER, MetaArg.LOGGER_QUEUE)
    }

    @classmethod
    def get_handler(cls, cmd: Command, streams_handler: StreamsHandler, template_resolver: TemplateResolver,
                    logger_queue: Queue, server_addr: str, workdir: str) -> AbstractCmdHandler:
        real_args = {
            MetaArg.STREAMS_HANDLER:   streams_handler,
            MetaArg.TEMPLATE_RESOLVER: template_resolver,
            MetaArg.HPCSTATS_RESOLVER: HPCStatsResolver(template_resolver.get_templ_sign(), logger_queue),
            MetaArg.IO_HANDLER:        IOHandler(workdir, logger_queue),
            MetaArg.LOGGER_QUEUE:      logger_queue,
            MetaArg.WORKDIR:           workdir,
            MetaArg.SERVER_ADDR:       server_addr
        }

        init_params = cls.__get_init_params(cmd, real_args)

        return cls.__handlers[cmd](*init_params)

    @classmethod
    def get_supported_commands(cls) -> frozenset:
        return frozenset(cls.__handlers.keys())

    @classmethod
    def __get_init_params(cls, cmd: Command, real_args: dict) -> tuple:
        init_params = []

        for meta_arg in cls.__args[cmd]:
            init_params.append(real_args[meta_arg])

        return tuple(init_params)
