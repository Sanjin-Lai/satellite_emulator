import socket
import PyInquirer
from interact import questions as qm
from command_client import message_format as mfm
from interact import validator as vm


class CommandClientUnit:

    def __init__(self, containers, name_to_id, server_listen_port: int, logger, available_name_prefix):
        """
        初始化可用的卫星的列表
        :param containers: 可用的卫星的map
        :param name_to_id: 从名称到id的映射
        :param server_listen_port: 服务器监听的端口
        :param logger: 日志记录
        :param available_name_prefix: 可以发送消息的节点的名称前缀
        """
        self.containers = containers
        self.name_to_id = name_to_id
        self.available_node_names = []
        self.server_ip_address = None
        self.server_port = server_listen_port
        self.server_address = None
        self.tcp_client_socket = None
        self.buffer_size = 1024
        self.logger = logger
        self.available_name_prefix = available_name_prefix
        self.get_available_names()

    def get_available_names(self):
        all_container_names = [item.container_name for item in self.containers.values()]
        for container_name in all_container_names:
            if container_name.find(self.available_name_prefix) != -1:
                self.available_node_names.append(container_name)

    def interact_with_user(self):
        """
        询问用户是否还需要进行信息的发送
        :return:
        """
        # 进行提问 - 进行某一颗节点的选择
        answers_for_node_selection = PyInquirer.prompt(qm.NODE_SELECTION_QUESTION)
        # 进行用户选择的节点的获取
        user_select_node = answers_for_node_selection["node"]
        # 进行用户选择的判断
        if user_select_node in self.available_node_names:
            self.logger.success(f"available to choose the node {user_select_node}")
        else:
            self.logger.error(f"not available to choose the node {user_select_node}")
            return
        # 根据名称进行地址的获取
        self.server_ip_address = self.containers[self.name_to_id[user_select_node]].addr_connect_to_docker_zero
        # 组建socket_address(ip, port)
        self.server_address = (self.server_ip_address, self.server_port)
        # 准备构建 socket 进行消息的发送
        self.tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置超时时间
        self.tcp_client_socket.settimeout(5)
        # 进行连接的建立 - 这个过程是阻塞的, 超过5s之后就将抛出 error
        self.logger.info(self.server_address)
        self.tcp_client_socket.connect(self.server_address)
        # 进行命令的发送
        self.send_command()

    def send_command(self):
        """
        向服务器端进行命令的发送
        :return:
        """
        # 首先进行信号的发送
        self.tcp_client_socket.connect(self.server_address)
        while True:
            # 首先询问要发送的命令的内容
            answers_for_message = PyInquirer.prompt(qm.SEND_MESSAGE_QUESTION)
            payload = answers_for_message["send_message"]
            # --------------------- create message ---------------------
            message = mfm.CommandMessage.NormalMessage(payload)
            # --------------------- create message ---------------------
            # -------------------- connect and send --------------------
            self.tcp_client_socket.send(bytes(message))
            self.recv_response()
            # -------------------- connect and send --------------------
            # 进行提问 - 是否继续
            answers_for_continue = PyInquirer.prompt(qm.SEND_CONTINUE_QUESTION)
            if answers_for_continue["continue"] == "yes":
                continue
            else:
                break
        self.tcp_client_socket.close()

    def recv_response(self):
        """
        服务器通常只返回很小的消息，所有我们只需要阻塞的 recv 一次即可。
        进行server_response
        :return:
        """
        try:
            server_response_bytes = self.tcp_client_socket.recv(self.buffer_size)
            message = mfm.CommandMessage.NormalMessage()
            message.load_bytes(server_response_bytes)
            self.logger.info(f"server_response: {message}")
        except Exception as e:
            self.logger.info(e)

