if __name__ == "__main__":
    import sys

    sys.path.append("../")

import socket
from udp_server import questions as qm
from PyInquirer import prompt


class CompleteUdpServer:
    def __init__(self):
        """
        初始化函数
        """
        self.selected_port = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.get_port()
        self.bind_and_receive_data()

    def get_port(self):
        """
        获取目的端口
        :return:
        """
        answers_for_port = prompt(qm.QUESTION_FOR_PORT)
        self.selected_port = int(answers_for_port["port"])

    def bind_and_receive_data(self):
        all_interface_address = "0.0.0.0"
        self.udp_socket.bind((all_interface_address, self.selected_port))
        while True:
            data, address = self.udp_socket.recvfrom(1024)
            data = data.decode()
            if data == "exit":
                break
            else:
                print(data, flush=True)


if __name__ == "__main__":
    complete_udp_server = CompleteUdpServer()
