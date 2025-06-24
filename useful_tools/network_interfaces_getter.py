class NetworkInterfacesGetter:
    @classmethod
    def get_specified_network_interface(cls, interface_name):
        """
        进行指定的接口的获取
        :param interface_name: 接口的名称
        :return:
        """
        f = open("/proc/net/dev")
        data = f.read()
        f.close()
        data = data.split("\n")[2:]
        for i in data:
            if len(i.strip()) > 0:
                x = i.split()
                # Interface |                        Receive                          |                         Transmit
                #   iface   | bytes packets errs drop fifo frame compressed multicast | bytes packets errs drop fifo frame compressed multicast
                current_interface_name = x[0][:len(x[0]) - 1]
                if current_interface_name == interface_name:
                    k = {
                        "interface": current_interface_name,
                        "tx": {
                            "bytes": int(x[1]),
                            "packets": int(x[2]),
                            "errs": int(x[3]),
                            "drop": int(x[4]),
                            "fifo": int(x[5]),
                            "frame": int(x[6]),
                            "compressed": int(x[7]),
                            "multicast": int(x[8])
                        },
                        "rx": {
                            "bytes": int(x[9]),
                            "packets": int(x[10]),
                            "errs": int(x[11]),
                            "drop": int(x[12]),
                            "fifo": int(x[13]),
                            "frame": int(x[14]),
                            "compressed": int(x[15]),
                            "multicast": int(x[16])
                        }
                    }
                    return k
        return None


if __name__ == "__main__":
    print(NetworkInterfacesGetter.get_specified_network_interface(interface_name="lo"))