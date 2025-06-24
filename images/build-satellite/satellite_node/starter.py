import os
import time
import threading
from satellite_node_decorator import signal_decorator as sdm
from satellite_node_useful_tools import logger as lm
from command_server import command_server_unit as csu
from satellite_node_useful_tools import envs_reader as erm
from netlink_client import netlink_client as ncm


class Starter:
    def __init__(self):
        """
        进行唯一的 logger 的创建
        """
        self.logger = lm.Logger().get_logger()
        self.envs_reader = erm.EnvsReader()
        self.server = csu.CommandServerUnit(listening_port=self.envs_reader.listening_port, my_logger=self.logger)
        self.netlink_userspace_client = ncm.NetlinkClient()

    def read_routes_and_insert_into_kernel(self):
        """
        将宿主机管理进程生成的路由信息读取并插入到内核之中。
        :return:
        """
        routes_configuration_file_source = f"/configuration/routes/{os.getenv('NODE_TYPE')}_{os.getenv('NODE_ID')}.conf"
        with open(routes_configuration_file_source, "r") as f:
            all_lines = f.readlines()
        # 接下来需要进行分析
        total_str = ""
        for single_line in all_lines:
            # 将目的节点的 id 进行提取
            start_index = single_line.find(":") + 1
            end_index = single_line.find(" ")
            destination_node_id = int(single_line[start_index:end_index])
            # 找到到目的节点的完整的序列
            remain_part = single_line[end_index+1:]
            # 进行所有的链路标识的查找
            sequence_identifiers = [int(item) for item in remain_part.split("->")]
            send_to_kernel_data = f"{os.getenv('NODE_ID')},"
            send_to_kernel_data += f"{destination_node_id},"
            send_to_kernel_data += f"{len(sequence_identifiers)},"
            for index, identifier in enumerate(sequence_identifiers):
                if index != len(sequence_identifiers) - 1:
                    send_to_kernel_data += f"{str(identifier)},"
                else:
                    send_to_kernel_data += str(identifier)
            send_to_kernel_data += "\n"
            total_str += send_to_kernel_data
        total_str.rstrip("\n")
        print(total_str, flush=True)
        self.netlink_userspace_client.send_netlink_data(total_str, message_type=ncm.NetlinkMessageType.CMD_INSERT_ROUTES)
        pass

    def start_server_as_a_thread(self):
        """
        开启服务器守护子线程，如果主线程 down 了，这个子线程跟着一起 down
        :return:
        """
        server_thread = threading.Thread(target=self.server.listen_at_docker_zero_address)
        server_thread.setDaemon(True)
        server_thread.start()

    @sdm.signal_decorator
    def never_stop_until_signal(self):
        """
        主线程，只有当收到了 signal 的时候 才会结束，否则反复进行睡觉。
        :return:
        """
        while True:
            time.sleep(60)

    def start_frr(self):
        """
        将文件复制到指定的位置，并调用命令 service frr start
        :return:
        """
        frr_configuration_file_source = f"/configuration/frr/{os.getenv('NODE_TYPE')}_{os.getenv('NODE_ID')}.conf"
        frr_configuration_file_dest = f"/etc/frr/frr.conf"
        copy_command = f"cp {frr_configuration_file_source} {frr_configuration_file_dest}"
        start_frr_command = "service frr start"
        os.system(copy_command)
        os.system(start_frr_command)

    def main_logic(self):
        """
        主逻辑：容器节点只需要调用这一个方法即可。
        :return:
        """
        # 开启服务器子线程
        try:
            # 进行 frr 路由软件的启动
            self.start_frr()
            self.read_routes_and_insert_into_kernel()
            self.start_server_as_a_thread()
            # 主线程
            self.never_stop_until_signal()
        except Exception as e:
            self.logger.error(e)


if __name__ == "__main__":
    starter = Starter()
    starter.main_logic()
