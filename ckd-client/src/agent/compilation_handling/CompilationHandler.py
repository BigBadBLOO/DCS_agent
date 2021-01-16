import json
import os
from multiprocessing import Queue

from src.agent.compilation_handling.CMakeHandler import CMakeHandler
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import LogLevel
from src.utils.Exceptions import ShellExecutionError
from src.utils.Executor import Executor
from src.utils.data_types.Task import Task
from src.utils.log.NamedLogWriter import NamedLogWriter


class CompilationHandler:
    __cmake_handler = None
    __executor = Executor()
    __cmake_version = ''

    def __init__(self, template_resolver: TemplateResolver, logger_queue: Queue,
                 workdir: str):
        self.__workdir = workdir
        self.__template_resolver = template_resolver
        self.__log_writer = NamedLogWriter(logger_queue, CompilationHandler.__name__)

        if self.__check_cmake():
            self.__cmake_handler = CMakeHandler(logger_queue, workdir, self.__cmake_version)

    def __check_cmake(self):
        """
        Check whether the machine supports building projects with CMake

        :return: True if CMake is supported, False otherwise
        """
        cmake_supported = True
        try:
            version = self.__executor.execute_shell_command('cmake --version')
            self.__cmake_version = version.split()[-1]
        except ShellExecutionError:
            cmake_supported = False

        return cmake_supported

    async def handle_compilation(self, task: Task, args: list):
        task.set_bin_name(
            os.path.join(
                task.path_to_task_bin(self.__workdir),
                task.get_name() + '.out'
            )
        )

        compilation_commands = self.__get_compile_cmds(task, args)

        compilation_output = await self.__executor.async_exec_cmds_with_wrapping(
            commands=compilation_commands,
            dir_to_use=task.path_to_task_bin(self.__workdir),
        )

        compilation_log_file = os.path.join(task.get_dir_name_for_task(self.__workdir), 'compilation.log')
        with open(compilation_log_file, 'w') as output_file:
            output_file.write(compilation_output)

        return

    @staticmethod
    def __is_c_compiler(compiler):
        c_compiler = 'cc' in compiler \
                     or '++' in compiler \
                     or 'xx' in compiler
        return c_compiler

    def __get_compile_cmds(self, task: Task, args: list):
        """
        Get compilation command to compile all of the task source files.

        :param task: related task
        :param args: additional arguments
        :return: list of compilation commands
        """
        compiler = task.get_compiler()
        if '' != compiler:
            bin_path = task.path_to_task_bin(self.__workdir)
            if not os.path.exists(bin_path):
                os.makedirs(bin_path)

            path = task.path_to_task_src(self.__workdir)
            if task.is_file_archive():
                if self.__cmake_handler is not None and task.uses_cmake():
                    if not self.__cmake_handler.is_cmake_target(path):
                        self.__cmake_handler.create_cmake_lists(task)
                    commands = self.__cmake_handler.get_compilation_commands_using_cmake(task)
                else:
                    commands = self.__no_cmake_compile_cmd(compiler, task, args)
            else:
                commands = self.__get_compile_cmd_for_single_file(compiler, task, args)

            self.__log_writer.log(json.dumps(commands, indent=4), level=LogLevel.DEBUG)
            return commands
        else:
            raise RuntimeError('No compiler is set for the task: {}'.format(task.get_name()))

    def __get_compile_cmd_for_single_file(self, compiler, task, args):
        files = os.path.join(
            task.path_to_task_src(self.__workdir),
            task.get_name()
        )

        command = self.__get_compile_cmd_for_args(compiler, files, task, args)
        return [command]

    def __no_cmake_compile_cmd(self, compiler, task: Task, args: list):
        files = self.__get_flat_archive_files(self.__is_c_compiler(compiler), task)

        command = self.__get_compile_cmd_for_args(compiler, files, task, args)
        return [command]

    @staticmethod
    def __get_compile_cmd_for_args(compiler, files, task, args):
        command = '{} {} -o {} {} >{} '.format(compiler, files, task.get_bin_name(),
                                               ' '.join(args), task.get_log_name())
        return command

    def __get_flat_archive_files(self, c_compiler, task: Task):
        """
        Get files list relevant for compilation

        :param c_compiler: whether the program would be compiled using C/C++ compiler
        :param task: task to handle
        :return: source files list
        """
        path = task.path_to_task_src(self.__workdir)
        dirfiles = os.listdir(path)
        if c_compiler:
            files = list(filter(lambda x: '.cxx' in x or '.cpp' in x or '.c' in x, dirfiles))
        else:
            files = list(filter(lambda x: '.f' in x, dirfiles))
        files = list(map(lambda x: os.path.join(path, x), files))
        files = ' '.join(files)
        return files
