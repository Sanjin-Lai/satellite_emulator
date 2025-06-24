import os.path
import time
from enum import Enum
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from useful_tools import logger as lm


class KernelLogReader(FileSystemEventHandler):
    class OpenModeChoice(Enum):
        """
        打开文件的方式，可以进行保留，可以进行删除
        """
        REMOVE = 1
        RETAIN = 2

    def __init__(self, file_path: str,
                 choice: OpenModeChoice,
                 kernel_pre_log_msg: str,
                 check_interval: float):
        """
        进行 KernelLogReader 的初始化
        :param file_path kernel.log 的文件路径
        :param choice 选择是进行截断还是进行补充
        :param kernel_pre_log_msg 判断这条消息是否是用户输出的消息的依据
        """
        self.file_path = file_path
        self.dir_path = os.path.dirname(file_path)
        self.choice = choice
        self.kernel_pre_log_msg = kernel_pre_log_msg
        self.last_file_length = None
        self.check_interval = check_interval
        self.logger = lm.Logger().get_logger()  # 进行日志记录器的获取
        self.truncate_file()

    def truncate_file(self):
        """
        进行文件的截断
        :return:
        """
        if self.choice == KernelLogReader.OpenModeChoice.REMOVE:
            with open(self.file_path, mode="w") as f:
                f.truncate()
        else:
            pass

    def on_modified(self, event):
        """
        一旦发生改变触发的事件
        :param event: 触发的事件
        :return:
        """
        if not event.is_directory:
            with open(self.file_path, "r") as file:
                if self.last_file_length is not None:
                    file.seek(self.last_file_length, 0)
                # 不断进行读取
                while True:
                    # 读取一行
                    single_line = file.readline()
                    # 如果这一行不为空
                    if single_line != "":
                        # 看是否有标识用户输出的
                        if single_line.find(self.kernel_pre_log_msg) != -1:
                            # 还需要将 linux 内核前面的多余的提示信息一并进行删除
                            single_line_strip = single_line.strip()
                            index = single_line_strip.find("]")
                            single_line_final = single_line_strip[index+1:]
                            self.logger.info(single_line_final)
                        # 如果没有则不进行输出
                        else:
                            pass
                    # 如果这一行为空
                    else:
                        break
                self.last_file_length = file.tell()

    def start_monitor(self):
        """
        启动监测器，每隔一段固定的时间进行一次检测
        :return:
        """
        observer = Observer()
        observer.schedule(self, path=self.dir_path, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
