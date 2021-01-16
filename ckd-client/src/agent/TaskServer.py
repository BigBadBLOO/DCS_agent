import asyncio
from multiprocessing import Queue

from src.agent.RequestHandler import RequestHandler
from src.utils.Enums import LogLevel
from src.utils.Executor import Executor
from src.utils.log.NamedLogWriter import NamedLogWriter


class TaskServer:
    __server = None
    __host = None
    __port = None
    __handler = None

    def __init__(self, host_n_port, writing_end_of_pipe, logger_queue: Queue, template_resolver=None, workdir='.'):

        self.__host = host_n_port[0]
        self.__port = host_n_port[1]

        self.__handler = RequestHandler(template_resolver, workdir, logger_queue, writing_end_of_pipe)
        self.__executor = Executor()

        self.__log_writer = NamedLogWriter(logger_queue, 'TaskServer')
        self.__log_writer.log('Created instance of TaskServer')

    def main_loop(self):
        """
        Synchronous method that starts the async method that will initialize the server

        :return: nothing
        """
        self.__log_writer.log('Starting TaskServer')
        exception = self.__executor.wrap_async_call(self.__loop)
        self.__log_writer.log('{}'.format(exception), LogLevel.ERROR)

    async def __loop(self):
        """
        Async method that actually initializes server

        :return: nothing
        """
        self.__log_writer.log('_loop called', LogLevel.DEBUG)
        self.__server = await asyncio.start_server(self.__handler.safe_handle, self.__host, self.__port)
        await self.__server.wait_closed()
        self.__log_writer.log('_loop exited', LogLevel.DEBUG)

    def shutdown(self):
        if self.__server is not None:
            self.__server.close()
        self.__log_writer.log('Shutting down TaskServer')


"""
if __name__ == '__main__':

    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = 'http://127.0.0.1:8888'

    serv = None
    _logger = None
    try:
        serv = TaskServer(
            host_n_port=('localhost', 80),
            server_addr=ip,
            workdir='tmp_dir',
        )
        _logger = serv.logger
        serv.main_loop()
    except Exception as e:
        _logger.log('Server error: ' + str(e), LogLevel.ERROR)
    finally:
        if serv is not None:
            serv.shutdown()
"""
