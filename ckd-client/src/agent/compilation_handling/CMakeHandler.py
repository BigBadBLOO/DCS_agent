import json
import os
import re
from multiprocessing import Queue

from src.utils.Enums import LogLevel
from src.utils.common import correct_line_breaks
from src.utils.data_types.Task import Task
from src.utils.log.NamedLogWriter import NamedLogWriter


class CMakeHandler:
    __C_MAKE_LISTS_TXT__ = 'CMakeLists.txt'

    def __init__(self, logger_queue: Queue, workdir: str, cmake_version):
        self.__workdir = workdir
        self.__log_writer = NamedLogWriter(logger_queue, 'CMakeHandler')
        self.__cmake_version = cmake_version

    def is_cmake_target(self, path: str):
        """
        Checks whether there is a CMakeLists.txt file in the archive

        :param path: path to archive contents
        :return: True if contains, False otherwise
        """
        return self.__C_MAKE_LISTS_TXT__ in os.listdir(path)

    def get_compilation_commands_using_cmake(self, task: Task):
        """
        Constructs commands to build CMake project and sets target executable name for task.
        For now supports only project build using Unix Makefiles.

        :param task: task to handle
        :return: command list to build CMake project
        """
        path = task.path_to_task_src(self.__workdir)
        bin_path = task.path_to_task_bin(self.__workdir)

        if not os.path.exists(bin_path):
            os.makedirs(bin_path)

        commands = [
            # invoking cmake in the 'bin' directory so that all of the generated files are inside 'bin' directory
            'cmake {} --warn-uninitialized --warn-unused-vars -Wno-dev'.format(path),
            # invoking build through the CMake build tool using appropriate tool for the system
            'cmake --build .',
        ]
        self.__log_writer.log(json.dumps(commands, indent=4), LogLevel.DEBUG)

        with open(os.path.join(path, self.__C_MAKE_LISTS_TXT__), 'r') as cmake_file:
            lines = cmake_file.read().splitlines()

        lines = list(filter(lambda x: 'project' in x, lines))
        # line = 'project(project_name)'
        lines = list(filter(lambda x: len(x) > 0, lines))
        lines = list(map(lambda x: re.split(r'[() ]', x), lines))
        self.__log_writer.log('LINES: {}'.format(lines))
        bin_name = os.path.join(bin_path, lines[0][1])
        task.set_bin_name(bin_name)

        return commands

    def create_cmake_lists(self, task: Task):
        """
        Generates CMakeLists.txt to make an archive into the CMake project

        :param task: task to handle
        :return: None
        """
        path = task.path_to_task_src(self.__workdir)
        cmake_lists_filename = os.path.join(path, self.__C_MAKE_LISTS_TXT__)

        main_file = self.__get_main_file_in_project(path)

        task_name = task.get_name()
        file_contents = [
            'cmake_minimum_required(VERSION {})'.format(self.__cmake_version),
            'project({})'.format(task_name),
            'SET(CMAKE_BUILD_TYPE Release)',
        ]

        extension = main_file.split('.')[-1]

        file_contents.append('file(GLOB SOURCES "./*.{}")'.format(extension))

        file_contents.append(' '.join(['add_executable('.format(task_name), '${SOURCES})']))

        dirs = self.__filter_dirs(path)

        include_dirs = list(filter(lambda x: 'include' in x, dirs))
        include_dirs = set(include_dirs)

        file_contents.append('include_directories({})'.format(', '.join(include_dirs)))

        dirs = set(dirs) - include_dirs

        for dir_name in dirs:
            file_contents.append('add_subdirectory({})'.format(dir_name))

        file_contents = '\n'.join(file_contents)
        file_contents = correct_line_breaks(file_contents)

        with open(cmake_lists_filename, 'w') as cmake_lists_file:
            cmake_lists_file.write(file_contents)

    @staticmethod
    def __get_main_file_in_project(path):
        # TODO: rework this solution. Maybe search for main() function in the source code files?
        return list(filter(lambda x: 'main' in x, os.listdir(path)))[0]

    @staticmethod
    def __filter_dirs(path):
        files = os.listdir(path)
        files = list(map(lambda x: os.path.join(path, x), files))

        return list(filter(lambda x: os.path.isdir(x), files))
