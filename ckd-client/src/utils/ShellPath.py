class ShellPath:

    def __init__(self, string_path: str):
        self.__path = string_path.strip('\r\n')

    def __str__(self):
        return self.__path
