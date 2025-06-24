class ContainerInformation:
    def __init__(self, *params):
        """
        进行容器id和状态的存储
        :param container_id: 容器的 id
        """
        self.container_id = None
        self.container_name = None
        self.addr_connect_to_docker_zero = None
        self.pid = None
        if len(params) == 1:  # 接受一个参数
            self.container_id = params[0]
            self.container_name = None
            self.addr_connect_to_docker_zero = None
        elif len(params) == 3:  # 接受三个参数
            self.container_id = params[0]
            self.container_name = params[1]
            self.addr_connect_to_docker_zero = params[2]
        else:  # 否则进行异常的抛出
            raise TypeError(f"only support parameters with 1 or 3 but {len(params)} are given")

    def __str__(self):
        """
        将对象信息作为字符串返回
        :return:
        """
        return (f"ID[{self.container_id}]|NAME[{self.container_name}]|ADDR[{self.addr_connect_to_docker_zero}]|"
                f"PID[{self.pid}]")