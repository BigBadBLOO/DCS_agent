import json
import urllib.parse as parser
import urllib.request as request
from multiprocessing import Queue

from src.agent.template_handling.HPCStatsResolver import HPCStatsResolver
from src.agent.template_handling.TemplateResolver import TemplateResolver
from src.utils.Enums import LogLevel
from src.utils.Exceptions import URLError
from src.utils.Executor import Executor
from src.utils.log.NamedLogWriter import NamedLogWriter


class HTTPSender:

    def __init__(self, server_addr: str, logger_queue: Queue, template_resolver: TemplateResolver,
                 hpc_stats_handler: HPCStatsResolver):
        self.__server_addr = server_addr
        self.__template_resolver = template_resolver
        self.__hpc_stats_handler = hpc_stats_handler
        self.__log_writer = NamedLogWriter(logger_queue, 'HTTPSender')
        self.__executor = Executor()
        self.__log_writer.log('Created instance with server addr: {}'.format(server_addr))

    def __get_csrf_cookie(self):
        """
        Acquire CSRF cookie from the server

        :return: CSRF cookie
        """
        cookie_handler = request.HTTPCookieProcessor()
        opener = request.build_opener(request.HTTPHandler(), cookie_handler)
        request.install_opener(opener)

        opener.open('{}'.format(self.__server_addr))

        # attempt to get the csrf token from the cookie jar
        csrf_cookie = None
        for cookie in cookie_handler.cookiejar:
            if cookie.name == 'csrftoken':
                csrf_cookie = cookie
                break
        if not csrf_cookie:
            raise IOError('No csrf cookie found')

        self.__log_writer.log('csrf_cookie: {}'.format(csrf_cookie), level=LogLevel.DEBUG)

        return csrf_cookie

    async def get_and_send_hpc_stats(self):
        """
        Get HPC stats like current CPU workload and send it to the server

        :return: string representation of the response
        """
        hpc_stats = await self.__executor.async_exec_shell_command(self.__template_resolver.get_hpc_stats_cmd())

        hpc_stats = self.__hpc_stats_handler.resolve_stats(self.__template_resolver.get_hpc_stats_pattern(), hpc_stats)
        hpc_stats = json.dumps(hpc_stats)

        try:
            cookie = await self.__executor.async_execution(self.__get_csrf_cookie)
        except Exception as e:
            raise URLError('while getting cookie: {}'.format(e))

        cookie = cookie.value.encode('ascii')
        encoded = parser.urlencode(
            dict(
                csrfmiddlewaretoken=cookie,
                data=hpc_stats
            )
        )
        encoded = encoded.encode()
        try:
            response = await self.__executor.async_execution(
                request.urlopen,
                '{}/hpcStats/'.format(self.__server_addr),
                encoded
            )
        except Exception as e:
            raise URLError('while updating info: {}'.format(e))

        return response.read().decode()
