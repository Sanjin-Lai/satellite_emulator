import multiprocessing
import time
import asyncio
from enum import Enum
from loguru import logger
from config import config_reader as crm
from docker_client import docker_client_http_impl as dchim
from docker_client import docker_namespace_builder as dnbm
from entities import constellation as cm
from useful_tools import progress_bar as pbm
from chain_maker_related import contract_manager as cmm
from entities import container_information as cim
from position_update import global_var as gv
from satellite_emulator.position_update import position_broadcaster as pbc


class LeoOrChainGenerator:
    class SatellitePosition:
        def __init__(self, stop_process_state, rcv_pipe):
            self.stop_process_state = stop_process_state
            self.rcv_pipe = rcv_pipe
            self.position_update_process = None
            self.gen_process()

        def gen_process(self):
            update_position_process = multiprocessing.Process(target=pbc.position_broadcast,
                                                              args=(self.stop_process_state, self.rcv_pipe))
            self.position_update_process = update_position_process

        def start_update_process(self):
            self.position_update_process.start()

        def stop_update_process(self):
            self.position_update_process.kill()

    class NetworkState(Enum):
        """
        链的状态，可能有 not_created | created | running | exited 四种状态
        """
        not_created = 0
        created = 1,
        running = 2,
        exited = 3

    def __init__(self, config_reader: crm.ConfigReader, my_logger: logger):
        """
        进行容器的初始化
        :param config_reader: 配置读取对象
        :param my_logger: 日志记录器
        """
        self.containers = {}  # 从容器 id 到容器信息的映射
        self.name_to_id = {}  # 从容器名到 id 的映射
        self.config_reader = config_reader
        self.my_logger = my_logger
        # self.contract_manager = cmm.ContractManager(cmc_exe_dir=config_reader.abs_of_cmc_dir, my_logger=my_logger)
        self.docker_client = dchim.DockerClientHttpImpl(self.config_reader.base_url)
        self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        self.logical_constellation = None
        self.container_prefix = None
        self.node_image_name = None
        self.number_of_containers = None
        self.set_prepare_param()

    # ----------------------------- 链管理相关  -----------------------------

    def set_prepare_param(self):
        """
        1、进行前缀的设置
        2、进行镜像名的设置
        3、进行节点数量的设置
        """
        # 进行节点 prefix 的确定：
        if self.config_reader.generate_leo_or_chain == "leo":
            self.container_prefix = "sat"
            self.node_image_name = self.config_reader.satellite_image_name
            self.number_of_containers = self.config_reader.number_of_satellites  # number_of_satellites 等于轨道数 * 每轨道的卫星的数量
        elif self.config_reader.generate_leo_or_chain == "chain":
            self.container_prefix = "consensus_node"
            self.node_image_name = self.config_reader.access_image_name
            self.number_of_containers = self.config_reader.number_of_satellites
        else:
            raise ValueError("generate_or_chain must be leo or chain")

    async def create_chain(self):
        """
        1. 根据配置信息 (环境变量、容器卷映射、端口映射等)，进行区块链上的节点的创建
        2. 将状态从 not_created 切换为 created 状态
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.not_created:
            tasks = []
            number_of_cm_node = self.config_reader.number_of_satellites
            self.logical_constellation = cm.Constellation(orbit_number=self.config_reader.num_of_orbit,
                                                          sat_per_orbit=self.config_reader.sat_per_orbit,
                                                          consensus_group_row=self.config_reader.consensus_group_row,
                                                          consensus_group_col=self.config_reader.consensus_group_col,
                                                          constellation_type=cm.Constellation.Type.WALKER_STAR_CONSTELLATION)
            self.logical_constellation.generate_satellites()
            self.logical_constellation.generate_isls_without_direction()
            self.logical_constellation.record_node_interfaces()

            # 进行路由的计算和存储
            self.logical_constellation.calculate_routes_with_all_nodes(
                generate_destination=self.config_reader.abs_of_routes_configuration,
                node_type=self.container_prefix)
            if self.container_prefix == "consensus_node":
                self.logical_constellation.modify_nodes_chainmaker_yml(
                    path_of_multi_node_config=f"{self.config_reader.abs_of_multi_node}/config")
            self.my_logger.info("Sat certs and ymlConfigs are modified!")
            # 进行ip地址的留存
            self.logical_constellation.generate_id_to_addresses_mapping(
                generate_destination=self.config_reader.abs_of_address_configuration,
                node_type=self.container_prefix)
            self.logical_constellation.generate_frr_files(
                generate_destination=self.config_reader.abs_of_frr_configuration,
                node_type=self.container_prefix)

            # docker_cpu_limit = int(self.config_reader.docker_cpu_limit*10e8)

            for index in range(0, number_of_cm_node):
                node_name = f"{self.container_prefix}{index}"
                # 如果进行的是长安链节点的创建
                if self.container_prefix == "consensus_node":
                    # 环境变量
                    # ---------------------------------------------------------
                    environment = [f"NODE_TYPE={self.container_prefix}",
                                   f"NODE_ID={index}",
                                   f"INTERFACE_COUNT={self.logical_constellation.satellites[index].interface_index}",
                                   f"LISTEN_ADDR={self.logical_constellation.satellites[index].ip_addresses[0]}"]
                    # ---------------------------------------------------------

                    # 容器卷映射
                    # ---------------------------------------------------------
                    volumes = [
                        f"{self.config_reader.abs_of_multi_node}/config/node{index + 1}:/accessauth/node_config/node{index + 1}",
                        f"{self.config_reader.abs_of_multi_node}/log/log{index + 1}:/accessauth/log",
                        f"{self.config_reader.abs_of_multi_node}/data/data{index + 1}:/accessauth/data",
                        f"{self.config_reader.abs_of_frr_configuration}:/configuration/frr",
                        f"{self.config_reader.abs_of_routes_configuration}:/configuration/routes",
                        f"{self.config_reader.abs_of_address_configuration}:/configuration/address"
                    ]
                    # ---------------------------------------------------------

                    # 端口映射
                    # ---------------------------------------------------------
                    exposed_ports = {
                        # f"{self.config_reader.p2p_port + (index)}/tcp": {},
                        f"{self.config_reader.rpc_port + index}/tcp": {},
                        f"{self.config_reader.signal_port + index}/tcp": {},
                    }
                    port_bindings = {
                        # f"{self.config_reader.p2p_port + (index)}/tcp": [
                        #     {
                        #         "HostIp": "",
                        #         "HostPort": f"{self.config_reader.p2p_port + (index)}"
                        #     }
                        # ]
                        # ,
                        f"{self.config_reader.rpc_port + index}/tcp": [
                            {
                                "HostIp": "",
                                "HostPort": f"{self.config_reader.rpc_port + index}"
                            }
                        ],
                        f"{self.config_reader.signal_port + index}/tcp": [
                            {
                                "HostIp": "",
                                "HostPort": f"{self.config_reader.signal_port + index}"
                            }
                        ]
                    }
                    # ---------------------------------------------------------

                    # 在容器内执行的命令
                    # ---------------------------------------------------------
                    command = [
                        "./chainmaker",
                        "start",
                        "-c",
                        f"../node_config/node{index + 1}/chainmaker.yml"
                    ]
                    # ---------------------------------------------------------

                    # 工作目录
                    # ---------------------------------------------------------
                    working_dir = "/accessauth/bin"
                    # ---------------------------------------------------------
                    task = asyncio.create_task(self.docker_client.create_container(image_name=self.node_image_name,
                                                                                   environment=environment,
                                                                                   container_name=node_name,
                                                                                   volumes=volumes,
                                                                                   exposed_ports=exposed_ports,
                                                                                   port_bindings=port_bindings,
                                                                                   command=command,
                                                                                   working_dir=working_dir))
                    tasks.append(task)
                elif self.container_prefix == "sat":
                    # 环境变量
                    # ---------------------------------------------------------
                    environment = [f"SATELLITE_NAME={node_name}",
                                   f"LISTENING_PORT={self.config_reader.listening_port}",
                                   f"NODE_TYPE={self.container_prefix}",
                                   f"NODE_ID={index}"]
                    # ---------------------------------------------------------
                    # 容器卷映射
                    # ---------------------------------------------------------
                    volumes = [
                        f"{self.config_reader.abs_of_frr_configuration}:/configuration/frr",
                        f"{self.config_reader.abs_of_routes_configuration}:/configuration/routes",
                        f"{self.config_reader.abs_of_address_configuration}:/configuration/address"
                    ]
                    # ---------------------------------------------------------
                    # 进行任务的创建
                    # ---------------------------------------------------------
                    task = asyncio.create_task(self.docker_client.create_container(image_name=self.node_image_name,
                                                                                   environment=environment,
                                                                                   container_name=node_name,
                                                                                   volumes=volumes))
                    # ---------------------------------------------------------
                    tasks.append(task)
                else:
                    raise ValueError("unsupported node type")
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="create chain process")
            for single_task in tasks:
                cm_node_container_id = single_task.result()
                self.containers[cm_node_container_id] = cim.ContainerInformation(cm_node_container_id)
            # 当创建完成之后，切换状态
            # 接着进行逻辑星座的生成, 生成是逻辑的一个拓扑，现在要进行物理的连接
            self.chain_state = LeoOrChainGenerator.NetworkState.created

    async def stop_chain(self):
        """
        进行容器的停止 - 只有位于运行状态的容器才能被停止，并将状态转换为停止状态。
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.running:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(
                    self.docker_client.stop_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="stop container process  ")
            self.chain_state = LeoOrChainGenerator.NetworkState.exited
        else:
            self.my_logger.error("satellite containers not in running state! cannot be stopped!")

    async def remove_chain(self):
        """
        进行容器的删除:
            1. 如果容器位于运行状态，那么需要先进行停止，然后进行删除，将状态转换为 NOT_CREATED
            2. 如果容器位于刚创建的状态，那么直接进行删除即可
            3. 如果容器位于停止状态，那么直接进行删除，将状态转换为 NOT_CREATED
        """
        start_time = time.time()
        # 如果容器位于运行状态的处理
        if self.chain_state == LeoOrChainGenerator.NetworkState.running:
            await self.stop_chain()
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove container process")
            self.containers = {}
            self.name_to_id = {}
            self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        # 如果容器位于创建状态的处理
        elif self.chain_state == LeoOrChainGenerator.NetworkState.created:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove container process")
            self.containers = {}
            self.name_to_id = {}
            self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        # 如果容器位于停止状态的处理
        elif self.chain_state == LeoOrChainGenerator.NetworkState.exited:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove container process")
            self.containers = {}
            self.name_to_id = {}
            self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        else:
            self.my_logger.error("satellite containers are already be removed!")
        end_time = time.time()
        self.my_logger.info(f"remove time elapsed {end_time - start_time} s")

    async def start_chain(self):
        """
        进行停止容器的恢复, 只有容器处于 STOPPED 或者 CREATED 的状态的时候才能够被 start 启动起来。
        :return:
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.exited or \
                self.chain_state == LeoOrChainGenerator.NetworkState.created:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(
                    self.docker_client.start_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="start container process ")
            self.chain_state = LeoOrChainGenerator.NetworkState.running
        else:
            self.my_logger.error("satellite containers not in stopped or created state! could not be started!")
        first_container = list(self.containers.values())[0]
        if not first_container.addr_connect_to_docker_zero:
            await self.inspect_chain_with_id()
        # 进行链接的创建
        print("start generate links......")
        await self.generate_connections()
        # lai xin
        gv.links_without_direction = self.logical_constellation.links_without_direction

    async def inspect_chain_without_id(self):
        """
        在尚且连容器 id 都不知道的情况下进行容器信息的获取
        :return:
        """
        response = await self.docker_client.inspect_all_containers()
        # here we need to analyze the containers
        single_container_info = None
        for single_container_info in response:
            container_id = single_container_info["Id"]
            self.containers[container_id] = cim.ContainerInformation(container_id)
        if single_container_info and (self.chain_state == LeoOrChainGenerator.NetworkState.not_created):
            self.chain_state = LeoOrChainGenerator.NetworkState[single_container_info["State"]]
        # 然后需要打印现有的卫星的信息
        self.my_logger.success(f"load existing satellites info status {self.chain_state}")
        await self.inspect_chain_with_id()
        self.print_chain_containers_info()

    async def inspect_chain_with_id(self):
        """
        进行卫星网络之中的容器的信息的检查
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.not_created:
            self.my_logger.error("satellite containers must be created before being inspected!")
        else:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.inspect_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="inspect container process")
            # 遍历所有已经完成的任务
            for single_finished_task in tasks:
                finished_task_result = single_finished_task.result()
                inspect_container_id = finished_task_result["ID"]
                inspect_container_addr = finished_task_result["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
                inspect_container_name = finished_task_result["Name"].lstrip("/")
                inspect_container_pid = finished_task_result["State"]["Pid"]
                self.containers[inspect_container_id].addr_connect_to_docker_zero = inspect_container_addr
                self.containers[inspect_container_id].container_name = inspect_container_name
                self.containers[inspect_container_id].pid = inspect_container_pid
                self.name_to_id[inspect_container_name] = inspect_container_id

    def print_chain_containers_info(self):
        """
        进行区块链之中容器的信息的打印
        """
        # 进行总长度的获取
        if len(self.containers.values()) > 0:
            total_length = len(str(list(self.containers.values())[0]))
        else:
            total_length = 97
        network_state = len(str(self.chain_state))
        single_part_str = "-" * ((total_length - network_state) // 2)
        print(f"{single_part_str}{self.chain_state}{single_part_str}")
        for container_info in self.containers.values():
            print(container_info)
        print(f"{single_part_str}{self.chain_state}{single_part_str}")

    # ----------------------------- 链管理相关  -----------------------------

    # ----------------------------- 创建链路相关  -----------------------------
    async def generate_connections(self):
        """
        进行节点间的连接
        """
        # 首先将网络命名空间放到合适的位置
        self.my_logger.info("move network namespaces of containers")
        dnbm.DockerNamespaceBuilder.build_network_namespace([item.pid for item in self.containers.values()])
        self.logical_constellation.bind_container_information(container_name_to_id=self.name_to_id,
                                                              containers=self.containers,
                                                              node_prefix=self.container_prefix)
        await self.logical_constellation.generate_veth_pairs_for_all_links(link_cmd_path=self.config_reader.abs_of_links_generator)
        # 生成完了之后，根据生成的逻辑星间链路进行实际的 veth 的创建

    # ----------------------------- 创建链路相关  -----------------------------
