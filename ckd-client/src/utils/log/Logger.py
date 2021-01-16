import logging
from logging.handlers import RotatingFileHandler as RFHLog

from src.utils.Enums import LogLevel


class AgentLogger:

    def __init__(self, filename: str, log_level: str, max_size_in_kilobytes: int, max_versions: int):
        rfh = RFHLog(filename, maxBytes=max_size_in_kilobytes * 1024, backupCount=max_versions)
        fmt = '%(asctime)s %(level)s %(message)s'
        logging.basicConfig(format=fmt, handlers=[rfh])

        self.__logger = logging.getLogger(__name__)
        if log_level == 'DEBUG':
            log_level = logging.DEBUG
        elif log_level == 'ERROR':
            log_level = logging.ERROR
        else:
            log_level = logging.INFO
        self.__logger.setLevel(log_level)

        self.__log_funcs = {
            LogLevel.DEBUG: self.__logger.debug,
            LogLevel.INFO:  self.__logger.info,
            LogLevel.ERROR: self.__logger.error
        }

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """
        Logs message at the set logging level

        :param message: message to log
        :param level: level to use: ['LogLevel.ERROR', 'LogLevel.INFO', 'LogLevel.DEBUG']
        :return: None
        """
        dct = {'level': level.value}

        self.__log_funcs[level](message, extra=dct)
