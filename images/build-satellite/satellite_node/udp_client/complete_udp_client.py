if __name__ == "__main__":
    import sys

    sys.path.append("../")
import socket
from enum import Enum
from PyInquirer import prompt
from udp_client import questions as qm


class Protocol(Enum):
    IP = 0,
    LIPSIN = 1


class CompleteUdpClient:
    def __init__(self):
        """
        初始化函数
        """
        self.selected_protocol = None
        self.selected_ip_address = None
        self.selected_port = None
        self.ip_mapping_file = "/configuration/address/address_mapping.conf"
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip_address_mapping = {}  # 从节点 id 到 ip 地址序列的一个映射
        self.read_address_mapping()
        self.get_protocol()
        self.get_destination()
        self.get_port()
        self.set_socket_options()
        self.send_data()

    def get_protocol(self):
        """
        进行用户选择的获取
        """
        answers_for_protocol = prompt(qm.QUESTION_FOR_PROTOCOL)
        if answers_for_protocol["protocol"] == "IP":
            self.selected_protocol = Protocol.IP
        elif answers_for_protocol["protocol"] == "LIPSIN":
            self.selected_protocol = Protocol.LIPSIN
        else:
            raise ValueError("unsupported protocol")

    def get_destination(self):
        """
        获取目的ip地址, 前提是一定要调用 read_address_mapping
        :return:
        """
        question_for_destination = qm.QUESTION_FOR_DESTINATION
        question_for_destination[0]["choices"] = list(self.ip_address_mapping.keys())
        answers_for_destination = prompt(question_for_destination)
        # find ip address according to the ip address_mapping
        selected_destination = answers_for_destination["destination"]
        self.selected_ip_address = self.ip_address_mapping[selected_destination][0]
        self.selected_ip_address = self.selected_ip_address[:self.selected_ip_address.find("/")]

    def get_port(self):
        """
        获取目的端口
        :return:
        """
        answers_for_port = prompt(qm.QUESTION_FOR_PORT)
        self.selected_port = int(answers_for_port["port"])

    def read_address_mapping(self):
        """
        进行 ip 地址映射的读取
        :return:
        """
        delimiter = "|"
        with open(self.ip_mapping_file, "r") as f:
            all_lines = f.readlines()
            for line in all_lines:
                # sat9|192.168.0.34/30|192.168.0.37/30
                items = line.split(delimiter)
                items[len(items) - 1] = items[len(items) - 1].rstrip("\n")
                self.ip_address_mapping[items[0]] = items[1:]

    def print_address_mapping(self):
        """
        进行 ip 地址映射的打印
        :return:
        """
        for item in self.ip_address_mapping.items():
            print(f"{item[0]}:{item[1]}", flush=True)

    def set_socket_options(self):
        """
        进行 socket 选项的设置
        :return:
        """
        if self.selected_protocol == Protocol.LIPSIN:
            # 进行 Lipsin 的标识，标识这个消息是 lipsin
            byte_array = bytearray([0x94, 0x8, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6])
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
            self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        else:
            pass

    def send_data(self):
        """
        利用获取到的目的 ip 地址和端口进行数据的发送
        :return:
        """
        while True:
            message = input("please input message: ")
            self.udp_socket.sendto(message.encode(), (self.selected_ip_address, self.selected_port))


if __name__ == "__main__":
    complete_udp_client = CompleteUdpClient()
