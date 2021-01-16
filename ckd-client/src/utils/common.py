import sys

from src.utils.Executor import Executor
from src.utils.ShellPath import ShellPath


def is_linux():
    return sys.platform.startswith('linux')


def has_list_elem(lst):
    """
    Checks whether list contains list elements

    :param lst: list possibly containing list elements
    :return: True if the list really contains list elements, False otherwise
    """
    return len(list(filter(lambda x: isinstance(x, type([])), lst))) > 0


def flatten_list(lst):
    """
    List flattening procedure
    (extracting all of the elements of the nested list elements into the resulting list)

    :param lst: list to flatten
    :return: flattened list
    """
    while has_list_elem(lst):
        buf = []
        for elem in lst:
            if isinstance(elem, type([])):
                for parts in elem:
                    buf.append(parts)
            else:
                buf.append(elem)
        lst = buf
    return lst


def correct_line_breaks(string):
    """
    Determine which line breaks are appropriate for the system
    and substitute them if necessary

    :param string: string with system-dependent line breaks
    :return: string with correct line breaks
    """
    is_linux_system = is_linux()
    is_linux_line_breaks = not string.split('\n')[0].endswith('\r')

    if (is_linux_system and is_linux_line_breaks) \
            or (not is_linux_system and not is_linux_line_breaks):
        # line breaks are correct for the system
        result = string
    elif is_linux_system and not is_linux_line_breaks:
        # OS is Linux and line breaks are for Windows
        result = '\n'.join(string.splitlines())
    else:
        # OS is Windows and line breaks are for Linux
        result = '\r\n'.join(string.splitlines())

    return result


def get_cur_shell_dir():
    executor = Executor()

    if is_linux():
        res = executor.execute_shell_command('pwd')
    else:
        res = executor.execute_shell_command('cd')

    res = '{}'.format(ShellPath(res))

    return res
