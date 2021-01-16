from multiprocessing import Queue

from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.utils.Enums import LogLevel
from src.utils.Exceptions import ShellExecutionError, MissingTemplateElement
from src.utils.Executor import Executor
from src.utils.data_types.Scheduler import Scheduler
from src.utils.data_types.Task import Task
from src.utils.log.NamedLogWriter import NamedLogWriter


class TemplateResolverBuilder:

    @staticmethod
    def build(workdir, scheds_list, logger_queue: Queue):
        """
        Return TemplateResolver with Scheduler model, appropriate for the system

        :param workdir: path to working directory
        :param scheds_list: known Scheduler list
        :param logger_queue: class instance that should be used for logging
        :return: TemplateResolver with appropriate Scheduler
        """
        log_writer = NamedLogWriter(logger_queue, 'TemplateResolverBuilder')
        template_resolver = None
        executor = Executor()
        for sched in scheds_list:  # type: Scheduler
            try:
                template_resolver = TemplateResolver(workdir, sched, logger_queue)
                caught = False
                cmd = template_resolver.get_hpc_stats_cmd()
                executor.execute_shell_command(cmd)
            except ShellExecutionError as error:
                log_writer.log('Scheduler {} wasn\'t found. Output: {}'.format(sched.get_name(), error))
                caught = True

            if not caught:
                return template_resolver
        raise RuntimeError('Unknown scheduler or no scheduler was found')


class TemplateResolver:
    """
    Class that handles the substitution template params for the real values.

    Manages both Scheduler command templates and Scheduler output template for the HPC statistics.
    """

    __templ_sign = '@'
    __sched = None  # type: Scheduler
    __io_handler = None

    def __init__(self, workdir: str, scheduler: Scheduler, logger_queue: Queue):
        self.workdir = workdir
        self.__sched = scheduler
        self.__hpc_stats_resolver = HPCStatsResolver(self.__templ_sign, logger_queue)
        self.__log_writer = NamedLogWriter(logger_queue, 'TemplateResolver')

    def __init_templ_dct(self, templ_dct, task: Task):
        """
        Function to initialize template dictionary with methods of the related Task object

        :param task: related task
        :return: nothing
        """
        templ_dct['__procnum__'] = task.get_procnum()
        templ_dct['__walltime__'] = task.get_walltime()
        templ_dct['__memory__'] = task.get_memory()
        templ_dct['__filename__'] = task.get_filename()
        templ_dct['__descname__'] = task.get_passport_name()
        templ_dct['__jobid__'] = task.get_jobid()
        templ_dct['__name__'] = task.get_name()
        templ_dct['__user__'] = task.get_user()
        templ_dct['__taskdir__'] = task.get_dir_name_for_task(self.workdir)
        templ_dct['__binname__'] = task.get_bin_name()
        templ_dct['__logname__'] = task.get_log_name()
        templ_dct['__workdir__'] = self.__get_workdir()

    def get_sched(self):
        return self.__sched

    def __get_workdir(self):
        return self.workdir

    def __substitute_template_params(self, templ: str, task: Task):
        """
        Main method of the TemplateResolver.
        Substitutes template elements for corresponding values.

        :param templ: template string
        :param task: related task
        :return: string with substituted template elements for real values
        """
        templ = templ.split(self.__templ_sign)
        templ_dct = {}
        res = []
        self.__init_templ_dct(templ_dct, task)
        for part in templ:
            if part in templ_dct.keys():
                to_add = templ_dct[part]
            else:
                to_add = part
            res.append(to_add)
            res = list(map(lambda x: str(x), res))
        return ''.join(res)

    def sched_uses_desc(self):
        return self.__sched.uses_desc()

    def get_run_for_task(self, task: Task):
        """
        Get 'run' command with real values instead of template parameters
        Also saves task passport

        :param task: related task
        :return: 'run' command with real values
        """
        return self.__substitute_template_params(self.__sched.get_run_cmd(), task)

    def resolve_jobid_from_output(self, cmd_output: str):
        template = self.__sched.get_jobid_template()
        template_list = template.split()
        cmd_output_list = cmd_output.strip('"\' ').split()

        pairs = list(zip(template_list, cmd_output_list))
        pairs = list(filter(lambda x: self.__templ_sign in x[0], pairs))

        if len(pairs) == 0:
            raise MissingTemplateElement(template, cmd_output)

        return pairs[0][1]

    def get_passport(self, task: Task):
        template = self.__sched.get_passport_template()

        template = template.splitlines()
        if 'mpi' in task.get_compiler().lower():
            template = self.__mpi_adapt_passport_template(template, '__NO_MPI__', '__MPI__')
        else:
            template = self.__mpi_adapt_passport_template(template, '__MPI__', '__NO_MPI__')

        template = '\n'.join(template)
        passport = self.__substitute_template_params(template, task)

        self.__log_writer.log('PASSPORT:\n{}'.format(passport), level=LogLevel.DEBUG)

        return passport

    @staticmethod
    def __mpi_adapt_passport_template(template, to_exclude, to_strip):
        template = list(filter(lambda x: to_exclude not in x, template))

        new_template = []
        for elem in template:
            if to_strip in elem:
                to_add = ' '.join(list(filter(lambda x: to_strip not in x, elem.split())))
            else:
                to_add = elem
            new_template.append(to_add)
        return new_template

    def get_stats_for_task(self, task: Task):
        """
        Get 'stats' command with real values instead of template parameters
        Also saves task passport

        :param task: related task
        :return: 'stats' command with real values
        """
        return self.__substitute_template_params(self.__sched.get_stats_cmd(), task)

    def get_cancel_for_task(self, task: Task):
        """
        Get 'cancel' command with real values instead of template parameters
        Also saves task passport

        :param task: related task
        :return: 'cancel' command with real values
        """
        return self.__substitute_template_params(self.__sched.get_cancel_cmd(), task)

    def get_hpc_stats_cmd(self):
        """
        Return Scheduler command that returns HPC statistics
        :return: Scheduler command that returns HPC statistics
        """
        return self.__sched.get_hpc_stats_cmd()

    def get_hpc_stats_pattern(self):
        return self.__sched.get_hpc_stats_pattern()

    def get_templ_sign(self):
        return self.__templ_sign
