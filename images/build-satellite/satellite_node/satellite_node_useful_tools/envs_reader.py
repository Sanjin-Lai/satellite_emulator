import os


class EnvsReader:
    def __init__(self):
        """
        进行环境变量的读取，并将其存储到自己的成员变量之中
        """
        self.listening_port = int(os.getenv("LISTENING_PORT"))
        if not all([self.listening_port]):
            raise TypeError("cannot get all the env list")
