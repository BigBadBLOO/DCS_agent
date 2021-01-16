import argparse
import itertools


class ConfigParser:
    file_prefix_char = '@'

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Run CKD HPC Agent',
            usage='python3 %(prog)s /path/to/config [--arg=<val> ...]. '
                  'For valid `arg` list please look at config/default.config',
            conflict_handler='resolve',
            prefix_chars='--',
            fromfile_prefix_chars='{}'.format(self.file_prefix_char)
        )
        self.parser.add_argument(
            '--server_addr', type=str, default=None,
            help='CKD web application server HTTP address with port'
        )
        self.parser.add_argument(
            '--work_dir', type=str, default='./agent_work_dir',
            help='Path to working directory where all of the task files will be stored'
        )
        self.parser.add_argument(
            '--log_dir', type=str, default='./agent_log_dir',
            help='Path to the directory where log files will be stored'
        )
        self.parser.add_argument(
            '--host', type=str, default='0.0.0.0',
            help='What IP should be given to the Agent socket'
        )
        self.parser.add_argument(
            '--port', type=int, default='9999',
            help='What port should be given to the Agent socket'
        )
        self.parser.add_argument(
            '--log_level', type=str, default='INFO',
            choices=['DEBUG', 'INFO', 'ERROR'],
            help='Level of logging that should be used'
        )
        self.parser.add_argument(
            '--log_max_kilobytes', type=int, default=500,
            help='How big log file must be to make a rollover'
        )
        self.parser.add_argument(
            '--log_version_count', type=int, default=3,
            help='How many log file rolled-over versions will be stored'
        )

    def parse(self, config_file, args):
        if config_file is not None and config_file != '':
            config = ['{}{}'.format(self.file_prefix_char, config_file)]
        else:
            config = []

        chain = list(itertools.chain(config, args))

        return self.parser.parse_args(chain)

    def print_help(self):
        self.parser.print_help()
