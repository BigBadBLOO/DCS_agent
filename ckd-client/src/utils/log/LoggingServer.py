import queue
from multiprocessing import Queue

from src.utils.Enums import LogLevel
from src.utils.log.Logger import AgentLogger


class LoggingServer:

    def __init__(self, in_queue: Queue, filename: str, log_level: str, max_size_in_kbs: int, max_versions: int):
        self.__queue = in_queue
        self.__looping = True
        self.__logger = AgentLogger(filename, log_level, max_size_in_kbs, max_versions)

    def main_loop(self):
        self.__logger.log('LoggingServer started')
        while self.__looping:
            try:
                self.__log()
            except queue.Empty:
                pass
        self.__logger.log('LoggingServer shutdown')

    def __log(self, should_block=True):
        data = self.__queue.get(block=should_block, timeout=2.0)
        message, level = self.__parse_incoming_data(data)
        self.__logger.log(message, level)

    @staticmethod
    def __parse_incoming_data(data):
        message = data['message']
        level = data['level']

        return message, level

    def shutdown(self):
        self.__looping = False

        data = {
            'message': 'LoggingServer shutting down',
            'level':   LogLevel.INFO
        }

        self.__queue.put(data)
