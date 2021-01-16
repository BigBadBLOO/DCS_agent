from multiprocessing import Queue

from src.agent.HTTPSender import HTTPSender
from src.agent.cmd_handlers.base_classes.BaseCmdHandler import BaseCmdHandler
from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.data_types.Task import Task
from src.utils.log.NamedLogWriter import NamedLogWriter


class HPCStatsCmdHandler(BaseCmdHandler):

    def __init__(self, template_resolver: TemplateResolver, hpc_stats_resolver: HPCStatsResolver,
                 logger_queue: Queue, server_addr: str):
        self.__server_addr = server_addr
        self.__template_resolver = template_resolver
        self.__hpc_stats_resolver = hpc_stats_resolver
        self.__log_writer = NamedLogWriter(logger_queue, 'HPCStatsCmdHandler')
        self.__sender = HTTPSender(self.__server_addr, logger_queue, self.__template_resolver,
                                   self.__hpc_stats_resolver)

    async def handle(self, task: Task, args: list):
        await self.__process_hpc_stats()

    async def __process_hpc_stats(self):
        """
        Method for getting HPC statistics like CPU usage

        :return: None
        """
        response = await self.__sender.get_and_send_hpc_stats()
        self.__log_writer.log('Server response for HPC stats: {}'.format(response))

        return None
