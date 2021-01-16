import os
import sys
from multiprocessing import Process, Pipe, Queue

# Append root dir to PATH to solve problems with import statements
sys.path.append(
    os.path.abspath(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )
    )
)

from src.agent.template_handling.TemplateResolver import TemplateResolverBuilder
from src.agent.StatusDaemon import StatusDaemon
from src.agent.TaskServer import TaskServer
from src.agent.ConfigParser import ConfigParser
from src.utils.Enums import LogLevel
from src.utils.log.NamedLogWriter import NamedLogWriter
from src.utils.SchedsDownloader import SchedsDownloader
from src.utils.log.LoggingServer import LoggingServer


class AgentBuilder:
    __config_parser = ConfigParser()

    @staticmethod
    def build(config_file, args):
        """
        Create Agent instance using the incoming configuration file and additional CLI params

        :param config_file: path to configuration file
        :param args: additional arguments passed through CLI
        :return: configured Agent instance
        """
        args = vars(AgentBuilder.__config_parser.parse(config_file, args))

        return Agent(
            workdir=args['work_dir'],
            logdir=args['log_dir'],
            server_addr=args['server_addr'],
            host_n_port=(args['host'], args['port']),
            log_level=args['log_level'],
            log_size_in_kbs=args['log_max_kilobytes'],
            log_versions=args['log_version_count']
        )

    @staticmethod
    def print_help():
        AgentBuilder.__config_parser.print_help()


class Agent:
    """
    HPC agent for the CKD web application.

    Consists of:
     TaskServer responsible for handling task related activities with update of HPC statistics when it's required;

     StatusDaemon responsible for fixed interval updates of the HPC statistics.
    """

    task_server_process_name = 'Agent.TaskServerProcess'
    status_daemon_process_name = 'Agent.StatusDaemonProcess'
    logging_server_process_name = 'Agent.LoggingServerProcess'
    log_file_name = 'Agent.log'

    def __init__(self, workdir, logdir, server_addr, host_n_port, log_level, log_size_in_kbs, log_versions):
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logdir = os.path.abspath(logdir)

        logging_queue = Queue()
        self.logging_server = LoggingServer(
            in_queue=logging_queue,
            filename=os.path.join(logdir, self.log_file_name),
            log_level=log_level,
            max_size_in_kbs=log_size_in_kbs,
            max_versions=log_versions
        )

        self.logging_server_process = Process(
            target=self.logging_server.main_loop,
            name=self.logging_server_process_name
        )

        self.__log_writer = NamedLogWriter(logging_queue, 'Agent')
        self.__log_writer.log('Initializing Agent')

        template_resolver = None
        if server_addr is not None:
            try:
                scheds = self.__init_scheds(server_addr)
                template_resolver = TemplateResolverBuilder.build(workdir, scheds, logging_queue)
            except Exception as error:
                message = 'Error during the initialization of TemplateResolver: {}'.format(error) + \
                          'Awaiting first connection to complete the initialization'
                self.__log_writer.log(message, level=LogLevel.INFO)
                pass

        if not os.path.exists(workdir):
            os.makedirs(workdir)
        workdir = os.path.abspath(workdir)

        recv_end, send_end = Pipe()

        self.task_server = TaskServer(
            host_n_port=host_n_port,
            template_resolver=template_resolver,
            workdir=workdir,
            writing_end_of_pipe=send_end,
            logger_queue=logging_queue
        )

        self.task_server_process = Process(
            target=self.task_server.main_loop,
            name=self.task_server_process_name,
        )

        self.status_daemon = StatusDaemon(
            server_addr=server_addr,
            template_resolver=template_resolver,
            reading_end_of_pipe=recv_end,
            logger_queue=logging_queue
        )

        self.status_daemon_process = Process(
            target=self.status_daemon.main_loop,
            name=self.status_daemon_process_name,
        )

        message = 'Created Agent instance with the following configuration:\n' + \
                  '\tworking directory:\t\t{}\n'.format(workdir) + \
                  '\tlog files directory:\t{}\n'.format(logdir) + \
                  '\tserver address:\t\t\t{}\n'.format(server_addr) + \
                  '\tsocket\'s host and port:\t{}\n'.format(host_n_port) + \
                  '\tlogging level:\t\t\t{}\n'.format(log_level) + \
                  '\tscheduler:\t\t\t\t{}\n'.format(
                      template_resolver.get_sched().get_name() if template_resolver is not None else 'None'
                  )
        self.__log_writer.log(message)

    def __init_scheds(self, scheds_source):
        """
        Acquire Schedulers' data

        :param scheds_source: where to acquire data (web application address)
        :return: list of Scheduler instances
        """
        self.__log_writer.log('Using DB for scheds data', LogLevel.DEBUG)
        downloader = SchedsDownloader(scheds_source)
        return downloader.get_scheds_from_db()

    def start(self):
        try:
            self.task_server_process.start()
            self.__log_writer.log('Started {}'.format(self.task_server_process_name), level=LogLevel.INFO)

            self.status_daemon_process.start()
            self.__log_writer.log('Started {}'.format(self.status_daemon_process_name), level=LogLevel.INFO)

            self.logging_server_process.run()
        except Exception as e:
            self.__log_writer.log('{}: {}'.format(type(e), e), level=LogLevel.ERROR)
            self.__log_writer.log('Agent shutdown due to error', level=LogLevel.ERROR)
            self.shutdown()

    def shutdown(self):
        self.task_server.shutdown()
        self.status_daemon.shutdown()
        self.__log_writer.log('Agent shutdown')

        if self.task_server_process.is_alive():
            self.__proper_process_termination(self.task_server_process)
        if self.status_daemon_process.is_alive():
            self.__proper_process_termination(self.status_daemon_process)

        self.logging_server.shutdown()
        if self.logging_server_process.is_alive():
            self.__proper_process_termination(self.logging_server_process)

    @staticmethod
    def __proper_process_termination(proc: Process):
        res = proc.join(1)
        if res is None:
            proc.terminate()


if __name__ == '__main__':
    builder = AgentBuilder()
    if len(sys.argv) < 2:
        builder.print_help()
        sys.exit(-1)

    agent = builder.build(sys.argv[1], sys.argv[2:])

    try:
        agent.start()
    finally:
        agent.shutdown()
