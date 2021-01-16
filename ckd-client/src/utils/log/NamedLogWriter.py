from multiprocessing import Queue

from src.utils.Enums import LogLevel


class NamedLogWriter:

    def __init__(self, logger_queue: Queue, log_id: str):
        self.__logger_queue = logger_queue
        self.__log_id = log_id

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        data = {
            'level':   level,
            'message': '{}: {}'.format(self.__log_id, message),
        }
        self.__logger_queue.put(data, block=True)
