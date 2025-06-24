from enum import Enum
import aiohttp
from loguru import logger


class DockerAsyncSocket:
    class HttpMethod(Enum):
        POST = 0
        GET = 1
        DELETE = 2

    def __init__(self, url):
        """
        :param url: 发送到服务器的 url
        """
        self.url = url
        self.headers = {'Content-Type': 'application/json'}

    async def create_container(self, url_parameters, body_parameters) -> int:
        """
        接收参数进行容器的创建
        :param url_parameters: request body 参数
        :param body_parameters: post payload 参数
        :return: None
        """
        final_url = f"{self.url}/containers/create?name={url_parameters['name']}"
        async with aiohttp.ClientSession() as session:
            async with session.post(final_url, json=body_parameters, headers=self.headers) as response:
                response_data = await response.json()
                if response.status != 201:
                    logger.error("create container failed!")
                else:
                    return response_data["Id"]

    async def stop_container(self, container_id):
        """
        调用 docker engine 原生接口进行容器的停止，并获取响应，判断操作是否成功
        :param container_id: 容器的id
        :return: None
        """
        final_url = f"{self.url}/containers/{container_id}/stop"
        async with aiohttp.ClientSession() as session:
            async with session.post(final_url, headers=self.headers) as response:
                await response.text()
                if response.status != 204:
                    logger.error(response.status)
                    logger.error("stop container failed!")

    async def start_container(self, container_id):
        """
        调用 docker engine 原生接口进行容器的启动，并获取响应，判断操作是否成功
        :param container_id: 容器的id
        :return: None
        """
        final_url = f"{self.url}/containers/{container_id}/start"
        async with aiohttp.ClientSession() as session:
            async with session.post(final_url) as response:
                await response.text()
                if response.status != 204:
                    logger.error("start container failed!")

    async def delete_container(self, container_id):
        """
        调用 docker engine 原生接口进行容器的删除，并获取响应，判断操作是否成功
        :param container_id: 容器的id
        :return: None
        """
        final_url = f"{self.url}/containers/{container_id}"
        async with aiohttp.ClientSession() as session:
            async with session.delete(final_url) as response:
                await response.text()
                if response.status != 204:
                    logger.error("start container failed!")

    async def inspect_container(self, container_id):
        """
        调用 docker engine 原生接口进行容器的检查
        :param container_id: 容器的id
        :return: 返回的是检查到的容器的信息
        """
        final_url = f"{self.url}/containers/{container_id}/json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=final_url) as response:
                result = await response.json()
                result["ID"] = container_id
                if response.status != 200:
                    logger.error("inspect container error!")
                else:
                    return result

    async def inspect_all_containers(self):
        """
        调用 docker engine 原生接口进行所有容器的信息的获取
        :return: 返回的是所有容器的信息
        """
        final_url = f"{self.url}/containers/json?all=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=final_url) as response:
                result = await response.json()
                if response.status != 200:
                    logger.error("inspect container error!")
                else:
                    return result
