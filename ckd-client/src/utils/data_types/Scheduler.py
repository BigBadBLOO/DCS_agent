import json

from src.utils.Enums import TaskStatus
from src.utils.common import flatten_list


class Scheduler:
    queued_status = 'queued_status'
    running_status = 'running_status'
    error_status = 'error_status'
    cancelled_status = 'cancelled_status'
    completed_status = 'completed_status'
    status_separator = ', '

    # its commands must contain	special symbols like @__procnum__@
    def __init__(self, sched_desc):
        self.__name = sched_desc['name']

        self.__run_task = sched_desc['run_task']
        self.__task_stats = sched_desc['task_stats']
        self.__cancel_task = sched_desc['cancel_task']
        self.__hpc_stats = sched_desc['hpc_stats']
        self.__passport = sched_desc.get('desc_file', '')
        self.__stats_pattern = sched_desc['stats_pattern']
        self.__jobid_template = sched_desc['jobid_template']

        self.__statuses = {
            TaskStatus.QUEUED:    self.__split_status(sched_desc[self.queued_status]),
            TaskStatus.RUNNING:   self.__split_status(sched_desc[self.running_status]),
            TaskStatus.ERROR:     self.__split_status(sched_desc[self.error_status]),
            TaskStatus.CANCELLED: self.__split_status(sched_desc[self.cancelled_status]),
            TaskStatus.COMPLETED: self.__split_status(sched_desc[self.completed_status])
        }

    @staticmethod
    def __split_status(statuses_str: str, separator: str = status_separator):
        return statuses_str.split(separator)

    def get_name(self):
        return self.__name

    def get_run_cmd(self):
        return self.__run_task

    def get_jobid_template(self):
        """
        SLURM example: 'Submitted job with id @__jobid__@'
        TORQUE example: '@__jobid__@'
        """
        return self.__jobid_template

    def get_stats_cmd(self):
        return self.__task_stats

    def get_cancel_cmd(self):
        return self.__cancel_task

    def uses_desc(self):
        return self.__passport != ''

    def get_passport_template(self):
        return self.__passport

    def is_status(self, string):
        return string in flatten_list(self.__statuses.values())

    def get_task_status(self, status: str) -> TaskStatus:
        for key in self.__statuses.keys():
            if status in self.__statuses[key]:
                return key
        raise RuntimeError('Unknown status {} for {} scheduler'.format(status, self.get_name()))

    def get_hpc_stats_cmd(self):
        return self.__hpc_stats

    def get_hpc_stats_pattern(self):
        return self.__stats_pattern

    def __str__(self):
        return self.to_json()

    def to_json(self):
        dct = {
            'name':                self.__name,
            'run_task':            self.__run_task,
            'jobid_template':      self.__jobid_template,
            'task_stats':          self.__task_stats,
            'cancel_task':         self.__cancel_task,
            self.queued_status:    self.status_separator.join(self.__statuses[TaskStatus.QUEUED]),
            self.running_status:   self.status_separator.join(self.__statuses[TaskStatus.RUNNING]),
            self.error_status:     self.status_separator.join(self.__statuses[TaskStatus.ERROR]),
            self.cancelled_status: self.status_separator.join(self.__statuses[TaskStatus.CANCELLED]),
            self.completed_status: self.status_separator.join(self.__statuses[TaskStatus.COMPLETED]),
            'desc_file':           self.__passport,
            'hpc_stats':           self.__hpc_stats,
            'stats_pattern':       self.__stats_pattern
        }
        return json.dumps(dct, indent=4)
