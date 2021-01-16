import itertools
import json
import os

from src.utils.Enums import TaskStatus


class Task:
    """
    Holds all of the required information about incoming task from web application
    """
    __tar_archives = ['tar', 'tgz', 'bz2', 'gz', 'xz']

    def __init__(self, dct: dict):
        self.__name = '_'.join(dct['name'].split(' '))
        self.__user = '_'.join(dct['username'].split(' '))

        self.__bin_name = dct.get('bin_name', '')
        self.__status = dct.get('status', TaskStatus.NOT_COMPILED)

        if self.__status != '':
            self.__status = TaskStatus(self.__status)
        else:
            self.__status = TaskStatus.NOT_COMPILED

        self.__memory = dct.get('memory', 0)
        self.__procnum = dct.get('procnum', 0)
        self.__walltime = dct.get('walltime', 0)
        self.__jobid = dct.get('jobid', '')
        self.__compiler = dct.get('compiler', '')
        self.__filename = dct.get('filename', '')
        self.__filesize = dct.get('filesize', '')
        self.__filesize = int(self.__filesize) if self.__filesize != '' else 0
        self.__use_cmake = dct.get('use_cmake', False)
        self.__error = dct.get('error', None)
        self.__passport = ''
        self.__log_name = ''
        self.__path = ''
        self.__validate()

    @staticmethod
    def get_empty_task():
        dct = {'name': '', 'username': ''}
        return Task(dct)

    @staticmethod
    def __get_extension(filename: str):
        if '.' not in filename:
            raise RuntimeError('Cannot determine file extension: no \'.\' in filename')

        extension = filename.split('.')[-1]

        if extension is None or extension == '':
            raise RuntimeError('Cannot determine file extension: empty extension')

        return extension

    def is_file_archive(self):
        extension = self.__get_extension(self.__filename)
        return extension in itertools.chain(['zip'], Task.__tar_archives)

    def set_passport_name(self, descname: str):
        self.__passport = descname

    def get_passport_name(self):
        return self.__passport

    def set_error(self, error: Exception):
        self.__error = error

    def get_error(self):
        return self.__error

    def set_status(self, status: TaskStatus):
        self.__status = status

    def get_status(self):
        return self.__status

    def get_str_status(self):
        return self.__status.value

    def set_bin_name(self, bin_name: str):
        self.__bin_name = bin_name

    def get_bin_name(self):
        return self.__bin_name

    def set_jobid(self, jobid: str):
        self.__jobid = jobid

    def get_jobid(self):
        return str(self.__jobid)

    def set_memory(self, mem: int):
        self.__memory = mem

    def get_memory(self):
        return self.__memory

    def set_procnum(self, num: int):
        self.__procnum = num

    def get_procnum(self):
        return self.__procnum

    def get_walltime(self):
        return self.__walltime

    def set_cmake_usage(self, should_use: bool):
        self.__use_cmake = should_use

    def uses_cmake(self):
        return self.__use_cmake

    def set_name(self, name: str):
        self.__name = name

    def get_name(self):
        return self.__name

    def get_user(self):
        return self.__user

    def set_filename(self, filename: str):
        self.__filename = filename

    def get_filename(self):
        return self.__filename

    def set_log_name(self, log_name: str):
        self.__log_name = log_name

    def get_log_name(self):
        return self.__log_name

    def set_path(self, path: str):
        self.__path = path

    def set_filesize(self, size: int):
        self.__filesize = size

    def get_filesize(self):
        if self.__filesize != 0:
            return self.__filesize
        elif self.__path != '':
            return os.path.getsize(self.__path)
        else:
            return 0

    def get_compiler(self):
        return self.__compiler

    def to_dict(self):
        res = {
            'name':      self.__name,
            'username':  self.__user,
            'status':    '{}'.format(self.__status.value),
            'memory':    self.__memory,
            'procnum':   self.__procnum,
            'walltime':  self.__walltime,
            'jobid':     self.__jobid,
            'filesize':  self.__filesize,
            'filename':  self.__filename,
            'bin_name':  self.__bin_name,
            'compiler':  self.__compiler,
            'use_cmake': self.__use_cmake,
            'error':     '{}'.format(self.__error),
        }

        return res

    def to_json(self, indent=0):
        return json.dumps(self.to_dict(), indent=indent)

    @staticmethod
    def from_json(json_string: str):
        return Task(json.loads(json_string))

    def __validate(self):
        """
        Perform validation of the constructed Task instance
        :return: nothing
        """
        assert isinstance(self.__status, TaskStatus), 'Bad type for \'status\': {}'.format(type(self.__status))
        assert isinstance(self.__compiler, type('str')), 'Bad type for \'compiler\': {}'.format(type(self.__compiler))
        assert isinstance(self.__jobid, type('str')), 'Bad type for \'jobid\': {}'.format(type(self.__jobid))
        assert isinstance(self.__filesize, type(0)), 'Bad type for \'filesize\': {}'.format(type(self.__filesize))
        assert isinstance(self.__procnum, type(0)), 'Bad type for \'procnum\': {}'.format(type(self.__procnum))
        assert isinstance(self.__memory, type(0)), 'Bad type for \'memory\': {}'.format(type(self.__memory))
        assert isinstance(self.__walltime, type(0)), 'Bad type for \'walltime\': {}'.format(type(self.__walltime))
        assert self.__filesize >= 0, 'Bad filesize value: {}. Expected value >= 0'.format(self.__filesize)
        assert self.__procnum >= 0, 'Bad procnum value: {}. Expected value >= 0'.format(self.__procnum)
        assert self.__memory >= 0, 'Bad memory value: {}. Expected value >= 0'.format(self.__memory)
        assert self.__walltime >= 0, 'Bad walltime value: {}. Expected value >= 0'.format(self.__walltime)

    def get_dir_name_for_task(self, workdir: str):
        """
        Get an absolute path to the directory with task-related files

        :param workdir: caller's working directory
        :return: path to task directory
        """
        curdir = os.path.abspath(workdir)
        curdir = os.path.join(curdir, self.__user)
        curdir = os.path.join(curdir, self.__name)
        return curdir

    def path_to_task_etc(self, workdir: str):
        target_dir = self.get_dir_name_for_task(workdir)
        target_dir = os.path.join(target_dir, 'etc')
        return target_dir

    def path_to_task_src(self, workdir: str):
        target_dir = self.get_dir_name_for_task(workdir)
        target_dir = os.path.join(target_dir, 'src')
        return target_dir

    def path_to_task_bin(self, workdir: str):
        target_dir = self.get_dir_name_for_task(workdir)
        target_dir = os.path.join(target_dir, 'bin')
        return target_dir

    def __str__(self):
        return self.to_json(indent=4)

    def exists(self, workdir: str):
        return os.path.exists(self.get_dir_name_for_task(workdir)) and \
               os.path.exists(self.path_to_task_src(workdir))
