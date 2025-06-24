from pyroute2.netlink import NLM_F_REQUEST, genlmsg
from pyroute2.netlink.generic import GenericNetlinkSocket

if __name__ == "__main__":
    import sys

    sys.path.append("../")
from satellite_node_useful_tools import logger as lm

CMD_UNSPEC = 0
CMD_REQ = 1


class NetlinkMessageType:
    CMD_UNSPEC = 0
    CMD_INSERT_ROUTES = 1  # 进行路由的插入
    CMD_CALCULATE_LENGTH = 2  # 进行长度的计算


# 消息的组成
class NetlinkMessageFormat(genlmsg):
    nla_map = (
        ('RLINK_ATTR_UNSPEC', 'none'),
        ('RLINK_ATTR_DATA', 'asciiz'),
        ('RLINK_ATTR_LEN', 'uint32'),
    )


class NetlinkClient(GenericNetlinkSocket):

    def __init__(self):
        super().__init__()
        self.logger = lm.Logger().get_logger()
        self.bind("EXMPL_GENL", NetlinkMessageFormat)

    def send_netlink_data(self, data: str, message_type: int):
        """
        进行数据的发送
        :param data: 要发送的数据
        :param message_type: 发送的消息的类型
        :return:
        """
        msg = NetlinkMessageFormat()
        msg["cmd"] = message_type
        msg["version"] = 1
        msg["attrs"] = [("RLINK_ATTR_DATA", data)]
        kernel_response = self.nlm_request(msg, self.prid, msg_flags=NLM_F_REQUEST)
        self.logger.success("-------RECEIVE KERNEL RESPONSE--------")
        data_part = kernel_response[0]
        self.logger.info(data_part.get_attr('RLINK_ATTR_LEN'))
        self.logger.info(data_part.get_attr('RLINK_ATTR_DATA'))
        self.logger.success("-------RECEIVE KERNEL RESPONSE--------")


if __name__ == "__main__":
    netlink_client = None
    try:
        netlink_client = NetlinkClient()
        netlink_client.send_netlink_data("hello world zhf!", message_type=NetlinkMessageType.CMD_CALCULATE_LENGTH)
    except Exception as e:
        netlink_client.logger.error(e)
    finally:
        if netlink_client is not None:
            netlink_client.close()
