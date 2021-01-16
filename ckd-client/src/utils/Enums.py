from enum import Enum


class Command(Enum):
    RUN = 'run'
    STATS = 'stats'
    CANCEL = 'cancel'
    RESULTS = 'results'
    SOURCES = 'sources'
    HPC_STATS = 'hpc_stats'


class MetaArg(Enum):
    STREAMS_HANDLER = 'streams_handler'
    TEMPLATE_RESOLVER = 'template_resolver'
    HPCSTATS_RESOLVER = 'hpcstats_resolver'
    IO_HANDLER = 'io_handler'

    LOGGER_QUEUE = 'logger'

    SERVER_ADDR = 'server_addr'
    WORKDIR = 'workdir'


class LogLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    ERROR = 'ERROR'


class TaskStatus(Enum):
    NOT_COMPILED = 'NOT_COMPILED'
    COMPILING = 'COMPILING'
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    ERROR = 'ERROR'
    CANCELLED = 'CANCELLED'
    COMPLETED = 'COMPLETED'
