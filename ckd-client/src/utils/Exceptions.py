from src.utils.Enums import Command


class CmdHandlerError(RuntimeError):

    def __init__(self, cmd, message):
        super().__init__('There was en error during handling of the \'{}\' command: {}'.format(cmd, message))


class ShellExecutionError(RuntimeError):

    def __init__(self, cmd, code, message):
        self.__cmd = cmd
        self.__retcode = code
        self.__message = message
        super().__init__('Command {} returned with exit status {}.\nOutput: {}'.format(
            self.__cmd, self.__retcode, self.__message
        ))


class NotOverriddenError(NotImplementedError):

    def __init__(self):
        super().__init__('Method should be implemented in a subclass')


class NotSupportedError(NotImplementedError):

    def __init__(self):
        super().__init__('Current functionality is not yet supported')


class UnknownCommand(RuntimeError):

    def __init__(self, cmd: Command):
        super().__init__('Unknown command: {}'.format(cmd))


class MissingTemplateElement(RuntimeError):

    def __init__(self, expected_format: str, output: str):
        super().__init__('Missing template element in supposedly template string:\nExpected: {}\nGot: {}'.format(
            expected_format,
            output)
        )


class URLError(RuntimeError):

    def __init__(self, message: str):
        super().__init__('Bad URL: {}'.format(message))
