import os

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.base_classes.BaseCmdHandler import BaseCmdHandler


class SendingCmdHandler(BaseCmdHandler):

    def __init__(self, streams_handler: StreamsHandler):
        self.__streams_handler = streams_handler

    async def send_files(self, results_file: str = '.'):
        """
        Send the archive with task execution results to the CKD web application

        :param results_file: path to the results file
        :return: nothing
        """
        size_in_bytes = str(os.path.getsize(results_file)).encode()
        await self.__streams_handler.write_data(size_in_bytes)

        with open(results_file, 'rb') as res:
            data = res.read()
            await self.__streams_handler.write_data(data)
