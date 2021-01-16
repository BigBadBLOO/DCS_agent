from src.utils.Executor import Executor


class AsyncFileHandler:
    __executor = Executor()

    async def async_write_file(self, filename: str, data: bytes):
        if isinstance(data, type('str')):
            data = data.encode('utf-8')

        with open(filename, 'wb') as file:
            await self.__executor.async_execution(lambda f, to_write: f.write(to_write), file, data)
        return

    async def async_read_file(self, filename: str):
        with open(filename, 'rb') as file:
            res = await self.__executor.async_execution(lambda f: f.read(), file)
        return res.decode()
