from useful_tools import kernel_log_reader as klrm
from interact import user_interface_for_kernel_reader as uim


if __name__ == "__main__":
    user_interface = uim.UserInterfaceForKernelReader()
    result = user_interface.get_kernel_log_reader_choices()
    kernel_log_reader = klrm.KernelLogReader(*result)
    kernel_log_reader.start_monitor()

