import asyncio
import json
from asyncio import StreamReader, StreamWriter
from multiprocessing import Queue

from src.utils.Enums import LogLevel
from src.utils.NetCommand import NetCommand
from src.utils.data_types.Task import Task
from src.utils.io.IOHandler import IOHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class StreamsHandler:
    __ERROR_DESC_START = 'Output:'

    def __init__(self, input_stream: StreamReader, output_stream: StreamWriter,
                 io_handler: IOHandler, logger_queue: Queue):
        self.__in_stream = input_stream
        self.__out_stream = output_stream
        self.__io_handler = io_handler
        self.__log_writer = NamedLogWriter(logger_queue, 'StreamsHandler')

    async def parse_incoming_data(self):
        incoming = await asyncio.wait_for(
            self.__in_stream.readuntil(NetCommand.separator),
            timeout=2.0
        )
        return NetCommand.parse_net_command(incoming)

    async def recv_file(self, task: Task) -> Task:
        """
        Receive incoming file from the reader channel

        :param task: related task
        :return: task
        """
        bufsize = task.get_filesize()
        in_file = await self.__in_stream.read(bufsize)
        recv_name = task.get_name()

        await self.__io_handler.write_recvd_data(task, recv_name, in_file)

        return task

    async def inform_client(self, task: Task, message: str, error: Exception = None) -> None:
        """
        Send information to the server using async writer channel

        :param task: related task
        :param error: related error message
        :param message: message to send
        :return: nothing
        """
        to_send = {'task_info': {}, 'message': '', 'error': ''}

        if task is not None:
            # Add info about the received task
            task_msg = {'name': task.get_name(), 'username': task.get_user(), 'status': task.get_str_status()}
            to_send['task_info'] = task_msg

        to_send['message'] = message

        levelname = LogLevel.DEBUG
        if error is not None and error != 'None':
            error = '{}'.format(error)
            idx = error.find(self.__ERROR_DESC_START)
            if idx >= 0:
                error = error[idx + len(self.__ERROR_DESC_START):]

            to_send['error'] = '{}'.format(error)
            to_send['task_info']['status'] = 'ERROR'
            levelname = LogLevel.ERROR
        self.__log_writer.log('Request response: {}'.format(json.dumps(to_send, indent=4)), level=levelname)

        try:
            # Sending response to CKD web application
            self.__out_stream.write(json.dumps(to_send, indent=4).encode())
            await self.__out_stream.drain()
        except Exception as e:
            self.__log_writer.log('Error occurred while responding to the CKD application: {}'.format(e))
        self.__log_writer.log('Response sent.', level=LogLevel.DEBUG)

    async def write_data(self, data: bytes):
        self.__out_stream.write(data)
        await self.__out_stream.drain()
