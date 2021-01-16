from multiprocessing import Queue

from src.agent.StreamsHandler import StreamsHandler
from src.agent.cmd_handlers.base_classes.SendingCmdHandler import SendingCmdHandler
from src.utils.Enums import Command
from src.utils.Exceptions import CmdHandlerError
from src.utils.data_types.Task import Task
from src.utils.io.IOHandler import IOHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class ResultsCmdHandler(SendingCmdHandler):

    def __init__(self, streams_handler: StreamsHandler, file_handler: IOHandler, logger_queue: Queue):
        self.file_handler = file_handler
        self.__log_writer = NamedLogWriter(logger_queue, 'ResultsCmdHandler')
        super().__init__(streams_handler)

    async def handle(self, task: Task, args: list):
        try:
            file = await self.__prepare_results_file(task)
            await self.send_files(file)

            self.__log_writer.log('Sent files')
        except Exception as e:
            raise CmdHandlerError(Command.RESULTS, '{}'.format(e))

        return task

    async def __prepare_results_file(self, task: Task):
        """
        Make zip archive containing all of the result and log files

        :param task: relevant task
        :return: path to the zip archive with execution results
        """
        return await self.file_handler.get_results(task)
