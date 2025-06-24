import os


class WorkDirManager:
    def __init__(self, change_dir: str):
        """
        进行工作目录上下文的初始化
        :param change_dir: 
        """
        self.change_dir = change_dir
        self.old_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.change_dir)
        # print(os.getcwd())

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_dir)
        # print(os.getcwd())


if __name__ == "__main__":
    with WorkDirManager(change_dir="/config"):
        print("hello")
        pass
