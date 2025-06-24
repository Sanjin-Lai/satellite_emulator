import ipaddress


class SubnetGenerator:
    @classmethod
    def generate_subnets(cls, base_network_tmp: str = "192.168.0.0/16"):
        """
        @param base_network_tmp: 基础网络
        @return: (子网, 第一个主机的ip地址, 第二个主机的ip地址)
        """
        base_network = ipaddress.ip_network(base_network_tmp)
        for single_subnet in base_network.subnets(new_prefix=30):
            split_part = str(single_subnet)[:-3].split(".")
            split_part[3] = str(int(split_part[3]) + 1)
            first_host_address = ".".join(split_part)
            split_part[3] = str(int(split_part[3]) + 1)
            second_host_address = ".".join(split_part)
            yield single_subnet, f"{first_host_address}/30", f"{second_host_address}/30"


if __name__ == "__main__":
    base_network_outer = "192.168.0.0/16"
    num_subnets_outer = 120
    subnets_result = SubnetGenerator.generate_subnets(base_network_tmp=base_network_outer)
    for i in range(20):
        print(next(subnets_result))
