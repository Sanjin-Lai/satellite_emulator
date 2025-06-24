import netifaces
import socket
import select
from command_server import message_format as mfm
from loguru import logger


class CommandServerUnit:
    def __init__(self, listening_port: int, my_logger):
        """
        进行命令接收服务器的初始化
        :param listening_port: 服务器监听的端口
        :param my_logger: 服务器使用的唯一的日志记录器。
        """
        self.docker_zero_interface_name = "eth0"
        self.docker_zero_interface_address = None
        self.tcp_connection_handler = None
        self.server_address = None
        self.listening_port = listening_port
        self.client_socket_list = []
        self.fileno_to_socket_map = {}
        self.epoll_event_loop = None
        self.buffer_size = 1024
        self.my_logger = my_logger
        self.get_docker_zero_address()

    def get_docker_zero_address(self):
        """
        拿到容器在 docker 0 上的地址
        :return:
        """
        all_interfaces = netifaces.interfaces()
        has_docker_zero_interface = False
        for interface in all_interfaces:
            if interface.startswith(self.docker_zero_interface_name):
                self.docker_zero_interface_address = interface
                has_docker_zero_interface = True
        if has_docker_zero_interface:
            # 获取 eth0 网络接口的 IP 地址
            addresses = netifaces.ifaddresses(self.docker_zero_interface_name)
            if netifaces.AF_INET in addresses:
                self.docker_zero_interface_address = addresses[netifaces.AF_INET][0]['addr']
            else:
                return f"No IPv4 address found for {self.docker_zero_interface_name}."
        else:
            return f"{self.docker_zero_interface_name} interface not found."

    def recv_command_messages(self, new_client_socket):
        """
        循环的进行命令消息的获取，由于 tcp 是可靠传输，所以不会存在多余的数据
        :param new_client_socket:
        :return: 收到的消息队列
        """
        all_messages = []
        all_bytes = bytes()
        while True:
            client_send_bytes = new_client_socket.recv(self.buffer_size)
            all_bytes += client_send_bytes
            if len(client_send_bytes) < self.buffer_size:
                break
        current_resolved_bytes_length = 0
        total_received_bytes_length = len(all_bytes)
        while current_resolved_bytes_length != total_received_bytes_length:
            message = mfm.CommandMessage.NormalMessage()
            resolved_bytes = message.load_bytes(all_bytes)
            all_bytes = all_bytes[resolved_bytes:]
            current_resolved_bytes_length += resolved_bytes
            all_messages.append(message)
        return all_messages

    def listen_at_docker_zero_address(self):
        """
        在拿到了容器连接到 docker 0 网络的接口的 ip 地址之后，我们只要监听指定地址的指定端口就可以了。
        :return:
        """
        self.server_address = (self.docker_zero_interface_address, self.listening_port)
        # 创建连接监听套接字
        self.tcp_connection_handler = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 绑定套接字
        self.tcp_connection_handler.bind(self.server_address)
        # 监听到来的套接字
        self.tcp_connection_handler.listen()
        # 创建 epoll
        self.epoll_event_loop = select.epoll()
        # 将监听套接字放到 epoll 之中, 监听可读事件
        self.epoll_event_loop.register(self.tcp_connection_handler.fileno(), select.EPOLLIN)
        # 将其放到 map 之中
        self.fileno_to_socket_map[self.tcp_connection_handler.fileno()] = self.tcp_connection_handler
        while True:
            # 默认为阻塞状态，直到 os 检测到 epoll 中数据发生修改，返回事件
            events = self.epoll_event_loop.poll()
            # 循环获取 epoll 返回的列表，即一写文件标识符可读或者可写的状态。
            for fd, event in events:
                if fd == self.tcp_connection_handler.fileno():
                    # 认为这个时候出现的是新的客户端的连接
                    new_client_socket, new_client_addr = self.tcp_connection_handler.accept()
                    # 设置成为非阻塞的状态
                    new_client_socket.setblocking(False)
                    self.epoll_event_loop.register(new_client_socket.fileno(), select.EPOLLIN)
                    # 将客户端套接字放到 epoll 之中，监听可读事件
                    self.fileno_to_socket_map[new_client_socket.fileno()] = new_client_socket
                elif event == select.EPOLLIN:
                    # 进行信息的接收
                    new_client_socket = self.fileno_to_socket_map[fd]
                    messages = self.recv_command_messages(new_client_socket)
                    self.execute_msgs(messages, fd)
                elif event == select.EPOLLHUP:  # 客户端断开事件，即客户端调用 close 关闭了写端，进入半开连接状态
                    # 我也进行写端的关闭
                    self.my_logger.info("客户端进行了连接的关闭")
                    self.fileno_to_socket_map[fd].close()
                    self.epoll_event_loop.unregister(fd)
                    del self.fileno_to_socket_map[fd]

    def execute_msgs(self, messages: list, fd: int):
        """
        消息队列的处理函数
        :param messages: 消息的数组
        :param fd: socket 对应的文件描述符
        :return:
        """
        client_socket = self.fileno_to_socket_map[fd]
        for single_normal_message in messages:
            server_response_message = mfm.CommandMessage.NormalMessage(f"client send string length: {str(single_normal_message.length)}")
            client_socket.send(bytes(server_response_message))


if __name__ == "__main__":
    command_server_unit = CommandServerUnit(30000, logger)
    command_server_unit.get_docker_zero_address()
    print(command_server_unit.docker_zero_interface_address)
