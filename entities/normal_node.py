from enum import Enum


class NormalNode:
    class Type(Enum):
        NORMAL_NODE = 1
        CONSENSUS_NODE = 2

        def __str__(self):
            if self.value == self.NORMAL_NODE:
                return "NORMAL_NODE"
            elif self.value == self.CONSENSUS_NODE:
                return "CONSENSUS_NODE"

    def __init__(self, node_id: int, node_type: Type):
        """
        进行节点的初始化
        :param node_id: 节点的 id
        :param node_type:  节点的类型
        """
        self.node_id = node_id
        self.node_type = node_type
        self.interface_index = 0
        self.container_id = "None"
        self.pid = "None"
        self.connect_subnet_list = []  # 节点连接到的所有子网络
        self.ip_addresses = {}  # 从接口索引 -> 接口对应的 ip 地址的映射

    def __str__(self):
        """
        返回节点代表的字符串
        :return:
        """
        return ("Node: " + str(self.node_id) +
                " ContainerId: " + self.container_id[:10] + "..." +
                " Pid: " + str(self.pid) +
                " Interface IP: " + str(self.ip_addresses))
