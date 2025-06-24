from docker_client import docker_client as dcm
from docker_client import docker_async_socket as dasm


class DockerClientHttpImpl(dcm.AbstractDockerClient):
    def __init__(self, url):
        """
        进行 docker client 的初始化
        :param url
        """
        super().__init__()
        self.docker_async_socket = dasm.DockerAsyncSocket(url)

    async def create_container(self, image_name: str,
                               container_name: str,
                               environment: list = None,
                               volumes: list = None,
                               exposed_ports=None,
                               port_bindings=None,
                               command=None,
                               working_dir=None) -> int:
        """
        根据特定的参数进行容器的创建
        :param cpu_limit: 容器cpu限制
        :param image_name: 镜像名称
        :param environment:  环境变量
        :param container_name: 容器的名字
        :param volumes: 容器数据卷
        :param exposed_ports: 暴露的端口
        :param port_bindings: 端口映射
        :param command: 执行的命令
        :param working_dir: 工作目录
        :return: 容器的id
        """
        url_parameters = {
            "name": container_name,
        }
        # ------------样板案例--------------
        # body_parameters = {
        #     "Image": image_name,
        #     "Env": environment,
        #     "Detach": True,
        #     "CapAdd": ["NET_ADMIN"],
        #     "ExposedPorts": exposed_ports,
        #     "Cmd": command,
        #     "WorkingDir": working_dir,
        #     "HostConfig": {
        #         "Binds": volumes,
        #         "PortBindings": port_bindings,
        #         "Privileged": True,
        #     }
        # }

        hostConfig = {
            "CapAdd": ["NET_ADMIN"],
            "Privileged": True
        }

        # if cpu_limit:
        #     hostConfig["NanoCpus"] = cpu_limit

        body_parameters = {
            "Image": image_name,
            "Detach": True,
            "HostConfig": hostConfig
        }
        if environment is not None:
            body_parameters["Env"] = environment
        if volumes is not None:
            body_parameters["HostConfig"]["Binds"] = volumes
        if exposed_ports is not None:
            body_parameters["ExposedPorts"] = exposed_ports
        if port_bindings is not None:
            body_parameters["HostConfig"]["PortBindings"] = port_bindings
        if command is not None:
            body_parameters["Cmd"] = command
        if working_dir is not None:
            body_parameters["WorkingDir"] = working_dir
        # ------------样板案例--------------

        return await self.docker_async_socket.create_container(url_parameters, body_parameters)

    async def start_container(self, container_id: str):
        """
        根据容器id恢复容器执行
        :param container_id:
        :return:
        """
        await self.docker_async_socket.start_container(container_id)

    async def stop_container(self, container_id: str):
        """
        根据容器id进行容器的停止
        :param container_id: 容器的id
        """
        await self.docker_async_socket.stop_container(container_id)

    async def delete_container(self, container_id: str):
        """
        根据容器id进行容器的删除
        :param container_id: 容器的id
        """
        await self.docker_async_socket.delete_container(container_id)

    async def inspect_container(self, container_id: str):
        """
        根据容器id进行容器的检查
        :param container_id: 容器的id
        :return: 返回的是容器的相关信息
        """
        response = await self.docker_async_socket.inspect_container(container_id)
        return response

    async def inspect_all_containers(self):
        """
        将系统之中现有的容器全部搜索到
        :return: 返回的是所有容器的相关信息
        """
        response = await self.docker_async_socket.inspect_all_containers()
        return response
