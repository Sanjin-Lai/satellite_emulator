from enum import Enum


class NormalLink:
    class Type(Enum):
        """
        星间链路的类型: 可能是 inter-orbit, 也可能是 intra-orbit
        """
        INTRA_ORBIT = 1
        INTER_ORBIT = 2
        NORMAL_LINK = 3

    def __init__(self, link_id: int, source_node, source_interface_index: int,
                 source_interface_address: str, dest_node, dest_interface_index: int,
                 dest_interface_address: str, link_type: Type):
        """
        进行星间链路的初始化
        :param link_id: 链路的 id
        :param source_node: 源节点
        :param source_interface_index: 链路所对应的源节点的接口索引
        :param source_interface_address: 这条链路所对应的源节点的接口 ip
        :param dest_node: 目的节点
        :param dest_interface_index: 目的节点所对应的接口的索引
        :param dest_interface_address: 这条链路所对应的目的节点的接口 ip
        :param link_type: 链路的类型 (是轨道间链路还是轨道内链路)
        """
        self.link_id = link_id
        self.source_node = source_node
        self.source_interface_index = source_interface_index
        self.source_interface_address = source_interface_address
        self.dest_node = dest_node
        self.dest_interface_index = dest_interface_index
        self.dest_interface_address = dest_interface_address
        self.link_type = link_type

    def __str__(self) -> str:
        """
        将链路对象转换为字符串
        :return: str
        """
        return (f"[{str(self.link_id)}]" + " " +
                "node " + str(self.source_node.node_id) + " " +
                "ethg[" + str(self.source_interface_index) + "]" + " " +
                "ipv4[" + self.source_interface_address + "]" +
                " <--> " + str(self.link_type) + " <--> " +
                "node " + str(self.dest_node.node_id) + " " +
                "ethg[" + str(self.dest_interface_index) + "]" + " " +
                "ipv4[" + self.dest_interface_address + "]")
