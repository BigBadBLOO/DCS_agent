import re
from multiprocessing import Queue

from src.utils.Enums import LogLevel
from src.utils.common import flatten_list
from src.utils.log.NamedLogWriter import NamedLogWriter


class HPCStatsResolver:

    __templ_dct = {
        # HPC statistics-related parameters
        '__irr__':      '__irr__',
        '__avail__':    '__avail__',
        '__total__':    '__total__',
        '__infrep__':   '__infrep__',
    }

    def __init__(self, templ_sign: str, logger_queue: Queue):
        self.templ_sign = templ_sign
        self.__log_writer = NamedLogWriter(logger_queue, 'HPCStatsResolver')

    def resolve_stats(self, pattern: str, hpc_stats: str):
        """
        Parse HPC statistics and get the required information

        :param pattern:
        :param hpc_stats: string with HPC statistics
        :return: dictionary containing relevant parts of the HPC statistics
        """
        try:
            pattern = pattern.split('\n')
            hpc_stats = hpc_stats.split('\n')

            avail_cpu_num, total_cpu_num = self.__handle_stats(pattern, hpc_stats)
        except Exception as e:
            self.__log_writer.log('{}'.format(e), level=LogLevel.ERROR)
            raise e

        res = {
            'total_cpu_num': total_cpu_num,
            'avail_cpu_num': avail_cpu_num
        }
        return res

    def __handle_stats(self, pattern, hpc_stats):
        pattern = self.__sync_length(hpc_stats, pattern)

        pairs = zip(pattern, hpc_stats)
        relevant = self.__leave_only_relevant(pairs)
        relevant = self.__handle_separators(relevant)
        return self.__compute_stats(relevant)

    def __sync_length(self, hpc_stats: list, pattern: list):
        """
        Append template pattern to synchronize its length with HPC statistics length

        :param hpc_stats: list with HPC statistics
        :param pattern: list with template pattern
        :return:
        """
        infrep = self.__templ_dct['__infrep__']
        can_inf_repeat = infrep in pattern
        length = len(hpc_stats)
        if len(pattern) < length and can_inf_repeat:
            infrep_only = list(filter(lambda x: infrep in x, pattern))[0]
            while len(pattern) < length:
                pattern.append(infrep_only)
        return pattern

    def __is_relevant(self, stat_line: str):
        """
        Determine whether the line is relevant for HPC statistics
        :param stat_line: line from the HPC statistics
        :return: True if relevant, False otherwise
        """
        return self.__templ_dct['__avail__'] in stat_line or self.__templ_dct['__total__'] in stat_line

    def __leave_only_relevant(self, pairs):
        """
        Filter out all of the irrelevant parts of the HPC statistics with respect to template

        :param pairs: list of pairs (statistics_element, template_element)
        :return: list of relevant pairs
        """
        # Leave only relevant lines
        relevant = list(filter(lambda x: self.__is_relevant(x[0]), pairs))

        # Leave only relevant parts of the line
        relevant = list(map(lambda x: zip(x[0].split(' '), x[1].split(' ')), relevant))
        new_relevant = []
        for zips in relevant:
            new_relevant.append(list(filter(lambda x: self.__is_relevant(x[0]), zips)))
        relevant.clear()

        # Get rid of empty parts
        new_relevant = list(filter(lambda x: len(x) > 0, new_relevant))

        # Flatten result so that it would contain only tuples
        new_relevant = flatten_list(new_relevant)
        return new_relevant

    def __extract_separators(self, new_relevant: list):
        """
        Determine symbols that separate relevant parts of HPC statistics

        :param new_relevant: list of relevant pairs
        :return: list of separators
        """
        buf = list(filter(lambda x: len(x) > 0, new_relevant[0][0].split(self.templ_sign)))

        stat_related = [
            self.__templ_dct['__avail__'],
            self.__templ_dct['__total__'],
            self.__templ_dct['__infrep__'],
            self.__templ_dct['__irr__']
        ]
        buf = ''.join(list(filter(lambda x: x not in stat_related, buf)))

        return buf

    def __handle_separators(self, relevant: list):
        """
        Get rid of the separators both in template and in HPC statistics element

        :param relevant: list of relevant pairs
        :return: list of relevant pairs with nested lists and no separators
        """
        separators = self.__extract_separators(relevant)
        relevant = list(map(lambda x: (re.split('[{}]'.format(separators), x[0]),
                                       re.split('[{}]'.format(separators), x[1])),
                            relevant))
        return relevant

    def __compute_stats(self, relevant: list):
        """
        Reduce the extracted statistics

        :param relevant: list of relevant parts of the HPC statistics
        :return: number of available CPUs, total number of CPUs
        """
        relevant = list(
            map(
                lambda x: dict(
                    zip(
                        # Remove '@' signs
                        list(map(lambda y: y.strip(self.templ_sign), x[0])),
                        # Convert strings to ints
                        list(map(lambda y: int(y), x[1]))
                    )
                ),
                relevant
            )
        )

        # TODO: if any other parts of HPC statistics becomes relevant this code should be changed
        total_cpu_num = 0
        avail_cpu_num = 0
        for stat in relevant:
            total_cpu_num += stat.get(self.__templ_dct['__total__'], 0)
            avail_cpu_num += stat.get(self.__templ_dct['__avail__'], 0)

        return avail_cpu_num, total_cpu_num

