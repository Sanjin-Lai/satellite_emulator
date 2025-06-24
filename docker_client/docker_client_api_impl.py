from docker_client import docker_client as dcm


class DockerClientApiImpl(dcm.AbstractDockerClient):
    def __init__(self):
        """
        进行 docker client 的初始化
        """
        super().__init__()

    def create_container(self, image_name: str,
                         environment: list,
                         container_name: str,
                         volumes: list,
                         exposed_ports,
                         port_bindings,
                         command,
                         working_dir) -> int:
        """
        根据特定的参数进行容器的创建
        :param image_name: 镜像名称
        :param environment:  环境变量
        :param container_name: 容器的名字
        :param volumes: 容器数据卷
        :param exposed_ports: 暴露的端口
        :param port_bindings: 端口映射
        :param command: 发送的命令
        :param working_dir: 工作目录
        :return: 容器的id
        """
        container_info = self.docker_manager.run(image=image_name, environment=environment,
                                                 name=container_name, volumes=volumes,
                                                 cap_add=["NET_ADMIN"], detach=True, privileged=True)
        container_id = container_info.id
        return container_id

    def start_container(self, container_id: str):
        """
        根据容器id恢复容器执行
        :param container_id:
        :return:
        """
        self.docker_manager.get(container_id).start()

    def stop_container(self, container_id: str):
        """
        根据容器id进行容器的停止
        :param container_id: 容器的id
        """
        self.docker_manager.get(container_id).stop()

    def delete_container(self, container_id: str):
        """
        根据容器id进行容器的删除
        :param container_id: 容器的id
        """
        self.docker_manager.get(container_id).remove()