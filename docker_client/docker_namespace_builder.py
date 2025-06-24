from useful_tools import root_authority_executor as raem


class DockerNamespaceBuilder:
    @classmethod
    def build_network_namespace(cls, pid_list: list):
        """
        利用容器的 pid 列表将容器的网络命名空间进行恢复
        :param pid_list: pid 列表
        """
        # 首先进行现有的网络命名空间的删除
        raem.RootAuthorityExecutor.execute(command=f"sudo rm -rf /var/run/netns/*")
        # 接着进行 pid 的遍历，并生成软链接
        # 创建的网络命名空间在/var/run/netns/路径下，但是docker默认将创建的ns链接文件隐藏起来了，导致无法使用 ip netns命令读取
        for pid in pid_list:
            source_file = f"/proc/{pid}/ns/net"  # 这是要用来产生软链接的源文件
            dest_file = f"/var/run/netns/{pid}"  # 这是生成的软链接
            full_command = f"sudo ln -s {source_file} {dest_file}"
            raem.RootAuthorityExecutor.execute(command=full_command)
