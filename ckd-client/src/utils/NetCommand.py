import json

from src.utils.Enums import Command
from src.utils.data_types.Task import Task


class NetCommand:
    separator = b'\0\0\0'

    @staticmethod
    def get_net_command(source, cmd, task, args=None):
        dct = {'source': source, 'cmd': cmd, 'task_info': task.to_dict(), 'args': args}
        return b''.join([json.dumps(dct, indent=4).encode(), NetCommand.separator])

    @staticmethod
    def parse_net_command(json_bytes_with_sep):
        json_string = json_bytes_with_sep.rstrip(b'\0').decode()
        dct = json.loads(json_string)

        source = dct['source'].rstrip('/')
        cmd = Command(dct['cmd'])

        if dct['cmd'] != 'hpc_stats':
            return source, cmd, Task(dct['task_info']), dct['args']
        else:
            return source, cmd, None, None
