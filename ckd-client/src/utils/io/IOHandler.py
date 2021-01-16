import os
import tarfile
import zipfile

from src.utils.Executor import Executor
from src.utils.common import correct_line_breaks
from src.utils.data_types.Task import Task
from src.utils.io.AsyncFileHandler import AsyncFileHandler
from src.utils.log.NamedLogWriter import NamedLogWriter


class IOHandler:
    __async_rw = AsyncFileHandler()
    info_filename = 'task.info'
    passport_filename = 'task.pass'

    def __init__(self, workdir, logger):
        self.workdir = workdir
        self.__log_writer = NamedLogWriter(logger, 'IOHandler')
        self.__executor = Executor()

    async def write_recvd_data(self, task: Task, recv_name: str, recvd_data: bytes):
        # Create directory for task files if it doesn't exist
        srcdir = task.path_to_task_src(self.workdir)
        if not os.path.exists(srcdir):
            os.makedirs(srcdir)

        # Write incoming file on disk
        recv_file = os.path.join(srcdir, recv_name)
        await self.__async_rw.async_write_file(recv_file, recvd_data)

        if task.is_file_archive():
            await self.__executor.async_execution(self.__handle_archive, task, srcdir, recv_file)

        return

    @staticmethod
    def __handle_archive(task: Task, curdir: str, recv_file: str):
        before = set(os.listdir(curdir))
        if '.zip' in task.get_filename():
            with zipfile.ZipFile(recv_file, mode='r') as zip_arc:
                arc_type = 'zip'
                zip_arc.extractall(path=curdir)
        else:
            with tarfile.open(name=recv_file, mode='r:*') as tar:
                arc_type = 'tar'
                tar.extractall(path=curdir)
        after = set(os.listdir(curdir))
        if after - (after ^ before) == set():
            # No changes in the directory
            raise RuntimeError('No extraction for {} archive'.format(arc_type))

        # There is no need for the archive to stay any longer
        os.remove(recv_file)

    async def write_task_passport(self, task: Task, passport: str):
        path_to_passport = task.path_to_task_etc(self.workdir)
        if not os.path.exists(path_to_passport):
            os.makedirs(path_to_passport)

        path_to_passport = os.path.join(path_to_passport, self.passport_filename)

        passport = correct_line_breaks(passport)

        await self.__async_rw.async_write_file(path_to_passport, passport)

        return path_to_passport

    async def save_task(self, task: Task):
        target_dir = task.path_to_task_etc(self.workdir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        task_info = os.path.join(target_dir, self.info_filename)
        await self.__async_rw.async_write_file(task_info, task.to_json(indent=4))

        return

    async def restore_task(self, task: Task):
        task_info = os.path.join(task.path_to_task_etc(self.workdir), self.info_filename)
        task = Task.from_json(await self.__async_rw.async_read_file(task_info))

        return task

    async def get_results(self, task: Task):
        zip_name = 'results.zip'
        path, files, zip_res = self.__extract_path_files_and_zip_res(task, zip_name)
        if zip_name not in files:
            files = list(
                # Leave only regular files
                filter(
                    lambda x: os.path.isfile(x) and 'sources' not in x,
                    # Make path to files absolute
                    map(
                        lambda x: os.path.join(path, x),
                        files
                    )
                )
            )

            await self.__executor.async_execution(self.__write_zip_file, files, zip_res)

        return zip_res

    async def get_sources(self, task: Task):
        zip_name = 'sources.zip'
        path, files, zip_res = self.__extract_path_files_and_zip_res(task, zip_name)
        if zip_name not in files:
            path = task.path_to_task_src(self.workdir)
            files = list(map(lambda x: os.path.join(path, x), os.listdir(path)))

            await self.__executor.async_execution(self.__write_zip_file, files, zip_res)

        return zip_res

    def __extract_path_files_and_zip_res(self, task: Task, zip_name: str):
        path = task.get_dir_name_for_task(self.workdir)

        if not os.path.exists(path):
            raise RuntimeError('Cannot get files for task {}. No directory is present for this task.'.format(
                task.get_name()
            ))

        files = os.listdir(path)
        zip_res = os.path.join(path, zip_name)
        return path, files, zip_res

    @staticmethod
    def __write_zip_file(files: list, zip_res: str):
        with zipfile.ZipFile(zip_res, mode='w') as zip_result:
            for file in files:
                zip_result.write(file, arcname=os.path.split(file)[-1])
