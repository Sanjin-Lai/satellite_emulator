from enum import Enum
import struct


class CommandMessage:
    class CommandType(Enum):
        # 报文的类型的定义
        NORMAL_MESSAGE = 1

    class NormalMessage:
        def __init__(self, *params):
            """
            进行数据包的初始化
            :param payload:  数据包的载荷部分
            """
            if len(params) == 0:
                self.type = None
                self.length = None
                self.payload = None
            elif len(params) == 1:
                self.type = int(CommandMessage.CommandType.NORMAL_MESSAGE.value)
                payload_in_bytes = params[0].encode(encoding="utf-8")
                self.length = len(payload_in_bytes)
                self.payload = payload_in_bytes
            else:
                raise TypeError(f"only support parameters with 0 or 1 but {len(params)} are given")

        def __bytes__(self):
            """
            将其转换为字节数组
            :return: 返回转换完成的字节数组
            """
            return struct.pack(f"<2I{self.length}s", self.type, self.length, self.payload)

        def load_bytes(self, bytes_tmp):
            """
            将传入的字节数组解析为对象的各个字段
            :param bytes_tmp: 这个消息对应的字节数组
            :return: 解析的字节的数量
            """
            self.type, self.length = struct.unpack("<2I", bytes_tmp[:8])
            self.payload = struct.unpack(f"<{self.length}s", bytes_tmp[8:8+self.length])[0]
            return 8 + self.length

        def __str__(self):
            """
            将数据包转换为对应的字符串
            :return: 数据包对应的字符串
            """
            return f"type:{self.type} | length:{self.length} | payload:{self.payload}"


if __name__ == "__main__":
    normal_message = CommandMessage.NormalMessage("zz123")
    bytes_pack = bytes(normal_message)
    print(bytes_pack)
    normal_message.load_bytes(bytes_pack)
    print(bytes(normal_message))

