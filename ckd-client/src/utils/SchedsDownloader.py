import json
from urllib import request

from src.utils.Exceptions import URLError
from src.utils.data_types.Scheduler import Scheduler


class SchedsDownloader:

    def __init__(self, server_addr: str):
        self.__server_addr = server_addr

    def get_scheds_from_db(self):
        """
        Get Scheduler's data from web application

        :return: list of Scheduler instances
        """
        try:
            response = request.urlopen('{}/schedsJSON/'.format(self.__server_addr))
        except Exception as e:
            raise URLError('{}'.format(e))

        desc_list = json.loads(response.read().decode())

        return list(map(lambda x: Scheduler(x), desc_list))
