import asyncio
import json
from multiprocessing import Queue
from multiprocessing.connection import Connection

from src.agent.HTTPSender import HTTPSender
from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import LogLevel
from src.utils.Executor import Executor
from src.utils.data_types.Scheduler import Scheduler
from src.utils.log.NamedLogWriter import NamedLogWriter


class StatusDaemon:
    __looping = None
    __stats_resolver = None

    def __init__(self, server_addr: str, logger_queue: Queue, template_resolver: TemplateResolver,
                 reading_end_of_pipe: Connection, err_threshold=10):
        self.__err_count = 0
        self.__err_threshold = err_threshold

        self.__reading_conn = reading_end_of_pipe

        self.__template_resolver = None
        self.sources = set()
        self.__senders = []
        if server_addr is not None and template_resolver is not None:
            self.__template_resolver = template_resolver
            self.__stats_resolver = HPCStatsResolver(template_resolver.get_templ_sign(), logger_queue)
            self.__senders.append(HTTPSender(server_addr, logger_queue, template_resolver, self.__stats_resolver))
            self.sources.add(server_addr)

        self.__executor = Executor()

        self.__logger_queue = logger_queue
        self.__log_writer = NamedLogWriter(logger_queue, 'StatusDaemon')

        self.__log_writer.log('Created instance of StatusDaemon')

    def main_loop(self):
        self.__log_writer.log('Starting StatusDaemon')
        self.__looping = True

        exception = self.__executor.wrap_async_call(self.__loop)
        self.__log_writer.log('{}'.format(exception), LogLevel.ERROR)

    async def __loop(self):
        self.__log_writer.log('_loop called', LogLevel.DEBUG)
        try:
            while self.__looping:
                try:
                    if self.__reading_conn.poll():
                        self.__handle_incoming_data()

                    response = await asyncio.gather(*[sender.get_and_send_hpc_stats() for sender in self.__senders])
                    self.__log_writer.log(response, LogLevel.DEBUG)
                    self.__err_count = 0
                except Exception as e:
                    self.__handle_exception(e)

                await asyncio.sleep(59)
        finally:
            self.shutdown()

    def __handle_incoming_data(self):
        if self.__template_resolver is None:
            workdir = self.__reading_conn.recv()
            sched_json = self.__reading_conn.recv()
            sched = Scheduler(json.loads(sched_json))
            self.__template_resolver = TemplateResolver(workdir, sched, self.__logger_queue)

        new_server_addr = self.__reading_conn.recv()
        if new_server_addr not in self.sources:
            new_sender = HTTPSender(new_server_addr, self.__logger_queue, self.__template_resolver,
                                    self.__stats_resolver)
            self.__senders.append(new_sender)

    def __handle_exception(self, e):
        self.__log_writer.log(e, LogLevel.ERROR)

    def shutdown(self):
        self.__looping = False
        self.__log_writer.log('Shutting down StatusDaemon')


"""
if __name__ == '__main__':

    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = 'http://127.0.0.1:8888'

    daemon = StatusDaemon(
        server_addr=ip,
        logger=AgentLogger('StatusDaemon.log', LogLevel.DEBUG, max_size_in_kilobytes=500, max_versions=2),
        template_resolver=TemplateResolver(os.getcwd(), 'irrelevant')
    )
    daemon.main_loop()
"""
