from collections import namedtuple
from interact import questions as qm
from useful_tools import kernel_log_reader as klrm
import PyInquirer


class UserInterfaceForKernelReader:
    def __init__(self):
        """
        内核读取用户界面的初始化
        """
        self.answers_for_kernel_log_reader = None
        self.get_user_choices()

    def get_user_choices(self):
        """
        让用户进行自己的选择的输入
        """
        self.answers_for_kernel_log_reader = PyInquirer.prompt(qm.KERNEL_LOG_READER_QUESTION)

    def get_kernel_log_reader_choices(self):
        """
        解析用户的选择
        :return:
        """
        # create named tuple
        Result = namedtuple("kernel_log_reader_result", "path choice preMsg interval")
        kernel_file_path = self.answers_for_kernel_log_reader["kernel_log_file_path"]
        remove_or_retain = klrm.KernelLogReader.OpenModeChoice.REMOVE \
            if self.answers_for_kernel_log_reader["remove_or_retain"] == "Remove" \
            else klrm.KernelLogReader.OpenModeChoice.RETAIN
        kernel_log_pre_msg = self.answers_for_kernel_log_reader["kernel_log_pre_msg"]
        check_interval = float(self.answers_for_kernel_log_reader["interval"])
        result = Result(kernel_file_path,
                        remove_or_retain,
                        kernel_log_pre_msg,
                        check_interval)
        return result
