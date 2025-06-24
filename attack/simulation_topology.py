import asyncio
import os
import threading
import time
import requests
from nsenter import Namespace
from multiprocessing import Queue
from enum import Enum
from loguru import logger
from matplotlib import pyplot as plt
from entities import normal_node as nnm
from entities import normal_link as nlm
from generator import subnet_generator as sgm
from visualizer import graph_visualizer as gvm
from config import config_reader as crm
from docker_client import docker_client_http_impl as dchim
from useful_tools import progress_bar as pbm
from entities import container_information as cim
from docker_client import docker_namespace_builder as dnbm
from useful_tools import root_authority_executor as raem
from chain_maker_related import contract_manager as cmm
from useful_tools import network_interfaces_getter as nigm


class SimulationTopology:
    class State(Enum):
        """
        链的状态，可能有 not_created | created | running | exited 四种状态
        """
        not_created = 0
        created = 1,
        running = 2,
        exited = 3

    def __init__(self, config_reader: crm.ConfigReader, my_logger: logger):
        """
        进行模拟拓扑的初始化
        :param config_reader: 配置读取
        :param my_logger: 日志记录器
        """
        self.total_packet_count = 0
        self.total_packet_size = 0
        self.config_reader = config_reader  # 配置读取者
        self.docker_client = dchim.DockerClientHttpImpl(self.config_reader.base_url)
        self.containers = {}  # 从容器 id 到容器信息的映射
        self.name_to_id = {}  # 从容器名到 id 的映射
        self.my_logger = my_logger
        self.state_of_simulation_topology = SimulationTopology.State.not_created
        self.subnet_generator = sgm.SubnetGenerator.generate_subnets(base_network_tmp="192.168.0.0/16")
        self.contract_manager = cmm.ContractManager(cmc_exe_dir=config_reader.abs_of_cmc_dir, my_logger=my_logger)
        # -----------------------------------所有的节点(包括共识节点和普通节点)---------------------------------------
        self.consensus_node_left_first = nnm.NormalNode(node_id=1, node_type=nnm.NormalNode.Type.CONSENSUS_NODE)
        self.consensus_node_left_second = nnm.NormalNode(node_id=2, node_type=nnm.NormalNode.Type.CONSENSUS_NODE)
        self.normal_node_middle_first = nnm.NormalNode(node_id=1, node_type=nnm.NormalNode.Type.NORMAL_NODE)
        self.normal_node_middle_second = nnm.NormalNode(node_id=2, node_type=nnm.NormalNode.Type.NORMAL_NODE)
        self.normal_node_middle_third = nnm.NormalNode(node_id=3, node_type=nnm.NormalNode.Type.NORMAL_NODE)
        self.consensus_node_right_first = nnm.NormalNode(node_id=3, node_type=nnm.NormalNode.Type.CONSENSUS_NODE)
        self.consensus_node_right_second = nnm.NormalNode(node_id=4, node_type=nnm.NormalNode.Type.CONSENSUS_NODE)
        self.consensus_nodes = [self.consensus_node_left_first,
                                self.consensus_node_left_second,
                                self.consensus_node_right_first,
                                self.consensus_node_right_second]
        self.normal_nodes = [self.normal_node_middle_first,
                             self.normal_node_middle_second,
                             self.normal_node_middle_third]
        self.all_nodes = self.consensus_nodes + self.normal_nodes
        # -----------------------------------所有的节点(包括共识节点和普通节点)---------------------------------------

        # -----------------------------------(左侧第一个共识节点 ---> 中间第一个节点)---------------------------------------
        subnet, first_address, second_address = next(self.subnet_generator)
        self.link_from_cn_one_to_nn_one = nlm.NormalLink(link_id=1,
                                                         source_node=self.consensus_node_left_first,
                                                         source_interface_index=self.consensus_node_left_first.interface_index,
                                                         source_interface_address=first_address,
                                                         dest_node=self.normal_node_middle_first,
                                                         dest_interface_index=self.normal_node_middle_first.interface_index,
                                                         dest_interface_address=second_address,
                                                         link_type=nlm.NormalLink.Type.NORMAL_LINK)
        self.consensus_node_left_first.ip_addresses[self.consensus_node_left_first.interface_index] = first_address
        self.normal_node_middle_first.ip_addresses[self.normal_node_middle_first.interface_index] = second_address
        self.consensus_node_left_first.connect_subnet_list.append(subnet)
        self.normal_node_middle_first.connect_subnet_list.append(subnet)
        self.consensus_node_left_first.interface_index += 1
        self.normal_node_middle_first.interface_index += 1
        # -----------------------------------(左侧第一个共识节点 ---> 中间第一个节点)---------------------------------------

        # -----------------------------------(左侧第二个共识节点 ---> 中间第一个节点)---------------------------------------
        subnet, first_address, second_address = next(self.subnet_generator)
        self.link_from_cn_two_to_nn_one = nlm.NormalLink(link_id=2,
                                                         source_node=self.consensus_node_left_second,
                                                         source_interface_index=self.consensus_node_left_second.interface_index,
                                                         source_interface_address=first_address,
                                                         dest_node=self.normal_node_middle_first,
                                                         dest_interface_index=self.normal_node_middle_first.interface_index,
                                                         dest_interface_address=second_address,
                                                         link_type=nlm.NormalLink.Type.NORMAL_LINK)
        self.consensus_node_left_second.ip_addresses[self.consensus_node_left_second.interface_index] = first_address
        self.normal_node_middle_first.ip_addresses[self.normal_node_middle_first.interface_index] = second_address
        self.consensus_node_left_second.connect_subnet_list.append(subnet)
        self.normal_node_middle_first.connect_subnet_list.append(subnet)
        self.consensus_node_left_second.interface_index += 1
        self.normal_node_middle_first.interface_index += 1
        # -----------------------------------(左侧第二个共识节点 ---> 中间第一个节点)---------------------------------------

        # ------------------------------------(中间第一个节点 ---> 中间第二个节点)-----------------------------------------
        subnet, first_address, second_address = next(self.subnet_generator)
        self.link_from_nn_one_to_nn_two = nlm.NormalLink(link_id=3,
                                                         source_node=self.normal_node_middle_first,
                                                         source_interface_index=self.normal_node_middle_first.interface_index,
                                                         source_interface_address=first_address,
                                                         dest_node=self.normal_node_middle_second,
                                                         dest_interface_index=self.normal_node_middle_second.interface_index,
                                                         dest_interface_address=second_address,
                                                         link_type=nlm.NormalLink.Type.NORMAL_LINK)
        self.normal_node_middle_first.ip_addresses[self.normal_node_middle_first.interface_index] = first_address
        self.normal_node_middle_second.ip_addresses[self.normal_node_middle_second.interface_index] = second_address
        self.normal_node_middle_first.connect_subnet_list.append(subnet)
        self.normal_node_middle_second.connect_subnet_list.append(subnet)
        self.normal_node_middle_first.interface_index += 1
        self.normal_node_middle_second.interface_index += 1
        # ------------------------------------(中间第一个节点 ---> 中间第二个节点)-----------------------------------------

        # ------------------------------------(中间第二个节点 ---> 右侧第一个共识节点)--------------------------------------
        subnet, first_address, second_address = next(self.subnet_generator)
        self.link_from_nn_two_to_cn_three = nlm.NormalLink(link_id=4,
                                                           source_node=self.normal_node_middle_second,
                                                           source_interface_index=self.normal_node_middle_second.interface_index,
                                                           source_interface_address=first_address,
                                                           dest_node=self.consensus_node_right_first,
                                                           dest_interface_index=self.consensus_node_right_first.interface_index,
                                                           dest_interface_address=second_address,
                                                           link_type=nlm.NormalLink.Type.NORMAL_LINK)
        self.normal_node_middle_second.ip_addresses[self.normal_node_middle_second.interface_index] = first_address
        self.consensus_node_right_first.ip_addresses[self.consensus_node_right_first.interface_index] = second_address
        self.normal_node_middle_second.connect_subnet_list.append(subnet)
        self.consensus_node_right_first.connect_subnet_list.append(subnet)
        self.normal_node_middle_second.interface_index += 1
        self.consensus_node_right_first.interface_index += 1
        # ------------------------------------(中间第二个节点 ---> 右侧第一个共识节点)--------------------------------------

        # ------------------------------------(中间第二个节点 ---> 右侧第二个共识节点)--------------------------------------
        subnet, first_address, second_address = next(self.subnet_generator)
        self.link_from_nn_two_to_cn_four = nlm.NormalLink(link_id=5,
                                                          source_node=self.normal_node_middle_second,
                                                          source_interface_index=self.normal_node_middle_second.interface_index,
                                                          source_interface_address=first_address,
                                                          dest_node=self.consensus_node_right_second,
                                                          dest_interface_index=self.consensus_node_right_second.interface_index,
                                                          dest_interface_address=second_address,
                                                          link_type=nlm.NormalLink.Type.NORMAL_LINK)
        self.normal_node_middle_second.ip_addresses[self.normal_node_middle_second.interface_index] = first_address
        self.consensus_node_right_second.ip_addresses[self.consensus_node_right_second.interface_index] = second_address
        self.normal_node_middle_second.connect_subnet_list.append(subnet)
        self.consensus_node_right_second.connect_subnet_list.append(subnet)
        self.normal_node_middle_second.interface_index += 1
        self.consensus_node_right_second.interface_index += 1
        # ------------------------------------(中间第二个节点 ---> 右侧第二个共识节点)--------------------------------------

        # --------------------------------------(中间第一个节点 ---> 中间第三个节点)----------------------------------------
        subnet, first_address, second_address = next(self.subnet_generator)
        self.link_from_nn_one_to_nn_three = nlm.NormalLink(link_id=6,
                                                           source_node=self.normal_node_middle_first,
                                                           source_interface_index=self.normal_node_middle_first.interface_index,
                                                           source_interface_address=first_address,
                                                           dest_node=self.normal_node_middle_third,
                                                           dest_interface_index=self.normal_node_middle_third.interface_index,
                                                           dest_interface_address=second_address,
                                                           link_type=nlm.NormalLink.Type.NORMAL_LINK)
        self.normal_node_middle_first.ip_addresses[self.normal_node_middle_first.interface_index] = first_address
        self.normal_node_middle_third.ip_addresses[self.normal_node_middle_third.interface_index] = second_address
        self.normal_node_middle_first.connect_subnet_list.append(subnet)
        self.normal_node_middle_third.connect_subnet_list.append(subnet)
        self.normal_node_middle_first.interface_index += 1
        self.normal_node_middle_third.interface_index += 1
        # --------------------------------------(中间第一个节点 ---> 中间第三个节点)----------------------------------------

        # ------------------------------------(将所有链路存储起来)--------------------------------------
        self.links_without_direction = [
            self.link_from_cn_one_to_nn_one,
            self.link_from_cn_two_to_nn_one,
            self.link_from_nn_one_to_nn_two,
            self.link_from_nn_two_to_cn_three,
            self.link_from_nn_two_to_cn_four,
            self.link_from_nn_one_to_nn_three
        ]
        # ------------------------------------(将所有链路存储起来)--------------------------------------

    def plot_graph(self):
        """
        进行图的绘制
        """
        node_ids = ["cn1", "cn2", "nn1", "nn2", "cn3", "cn4"]
        legend_labels = {'blue': 'Consensus Nodes', 'orange': 'Normal Nodes'}
        legend_handles = [plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=color, markersize=10, label=label)
                          for color, label in legend_labels.items()]
        edges = []
        for link in self.links_without_direction:
            if link.source_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
                first_node_prefix = "nn"
            else:
                first_node_prefix = "cn"
            if link.dest_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
                second_node_prefix = "nn"
            else:
                second_node_prefix = "cn"
            edges.append(
                (f"{first_node_prefix}{link.source_node.node_id}", f"{second_node_prefix}{link.dest_node.node_id}"))
        gvm.GraphVisualizer.plot_graph(nodes=node_ids,
                                       # edges=[(item.source_node.node_id, item.dest_node.node_id) for item in
                                       #        self.links_without_direction],
                                       edges=edges,
                                       topology_type=gvm.GraphVisualizer.Type.TEST_TOPOLOGY,
                                       node_colors=["blue", "blue", "orange", "orange", "blue", "blue"],
                                       node_size=500,
                                       legend_handles=legend_handles)

    def modify_nodes_chainmaker_yml(self):
        path_of_multi_node_config = f"{self.config_reader.abs_of_multi_node}/config"
        for consensus_node in self.consensus_nodes:
            new_seeds = []
            full_path_of_chainmaker_yml = f"{path_of_multi_node_config}/node{consensus_node.node_id}/chainmaker.yml"
            with open(full_path_of_chainmaker_yml, "r") as f:
                full_text = f.read()
            with open(full_path_of_chainmaker_yml, "w") as f:
                start_index = full_text.find("seeds:") + 7
                end_index = full_text.find("# Network tls settings") - 4
                front_part = full_text[:start_index]
                front_part = front_part.replace("listen_addr: /ip4/0.0.0.0/tcp/",
                                                f"listen_addr: /ip4/{consensus_node.ip_addresses[0][:-3]}/tcp/")
                end_part = full_text[end_index:]
                seeds = full_text[start_index:end_index].split("\n")
                for index, seed in enumerate(seeds):
                    new_seed = seed.replace("10.134.180.145", self.consensus_nodes[index].ip_addresses[0][:-3])
                    new_seeds.append(new_seed)
                middle_part = "\n".join(new_seeds)
                final_text = front_part + middle_part + end_part
                f.write(final_text)

    def generate_frr_files(self):
        generate_destination = self.config_reader.abs_of_frr_configuration
        if not os.path.exists(generate_destination):
            os.system(f"mkdir -p {generate_destination}")
        for single_node in self.all_nodes:
            if single_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
                node_prefix = "normal_node"
            elif single_node.node_type == nnm.NormalNode.Type.CONSENSUS_NODE:
                node_prefix = "consensus_node"
            else:
                raise ValueError("unexpected node type")
            with open(f"{generate_destination}/"
                      f"{node_prefix}_{single_node.node_id}.conf", "w") as f:
                full_str = \
                    f"""frr version 7.2.1 
frr defaults traditional
hostname satellite_{single_node.node_id}
log syslog informational
no ipv6 forwarding
service integrated-vtysh-config
!
router ospf
    redistribute connected
"""
                for connected_subnet in single_node.connect_subnet_list:
                    full_str += f"\t network {connected_subnet} area 0.0.0.0\n"
                full_str += "!\n"
                full_str += "line vty\n"
                full_str += "!\n"
                f.write(full_str)

    async def create_topology(self):
        """
        1. 根据配置信息 (环境变量、容器卷映射、端口映射) 进行节点的创建
        2. 将状态从 not_created 切换为 created 状态
        """
        if self.state_of_simulation_topology == SimulationTopology.State.not_created:
            tasks = []
            number_of_consensus_nodes = len(self.consensus_nodes)
            consensus_image_name = self.config_reader.chain_image_name
            self.modify_nodes_chainmaker_yml()  # 进行 chainmaker.yml 的生成
            self.generate_frr_files()  # 进行 frr 的生成
            # ------------------------------- (进行共识节点的创建) ----------------------------------
            for index in range(1, number_of_consensus_nodes + 1):
                # 容器的名称
                consensus_node_name = f"consensus-node{index}"

                # 环境变量
                # - 传入 NODE_ID 的作用是方便进行 frr 配置文件的读取
                # - 传入 INTERFACE_COUNT 的作用是方便进行 interface 的检测，检测到了之后再启动 rpc_server
                # -------------------------------------------------------------------------------
                environment = [f"NODE_TYPE=consensus_node",
                               f"NODE_ID={index}",
                               f"INTERFACE_COUNT={self.consensus_nodes[index - 1].interface_index}",
                               f"LISTEN_ADDR={self.consensus_nodes[index - 1].ip_addresses[0]}"]
                # -------------------------------------------------------------------------------

                # 容器卷映射
                # -------------------------------------------------------------------------------
                volumes = [
                    f"{self.config_reader.abs_of_multi_node}/config/node{index}:/chainmaker-go/config/wx-org{index}.chainmaker.org",
                    f"{self.config_reader.abs_of_multi_node}/data/data{index}:/chainmaker-go/data",
                    f"{self.config_reader.abs_of_multi_node}/log/log{index}:/chainmaker-go/log",
                    f"{self.config_reader.abs_of_frr_configuration}:/configuration/frr"
                ]
                # -------------------------------------------------------------------------------

                # 端口映射
                # -------------------------------------------------------------------------------
                exposed_ports = {
                    # f"{self.config_reader.p2p_port + (index - 1)}/tcp": {},
                    f"{self.config_reader.rpc_port + (index - 1)}/tcp": {},
                }
                port_bindings = {
                    # f"{self.config_reader.p2p_port + (index - 1)}/tcp": [
                    #     {
                    #         "HostIp": "",
                    #         "HostPort": f"{self.config_reader.p2p_port + (index - 1)}"
                    #     }
                    # ]
                    # ,
                    f"{self.config_reader.rpc_port + (index - 1)}/tcp": [
                        {
                            "HostIp": "",
                            "HostPort": f"{self.config_reader.rpc_port + (index - 1)}"
                        }
                    ]
                }
                # -------------------------------------------------------------------------------

                # 在容器内执行的命令
                # -------------------------------------------------------------------------------
                command = [
                    "./chainmaker",
                    "start",
                    "-c",
                    f"../config/wx-org{index}.chainmaker.org/chainmaker.yml"
                ]
                # f"./chainmaker start -c ../config/wx-org{index}.chainmaker.org/chainmaker.yml"
                # -------------------------------------------------------------------------------

                # 工作目录
                # ---------------------------------------------------------
                working_dir = "/chainmaker-go/bin"
                # ---------------------------------------------------------

                task = asyncio.create_task(self.docker_client.create_container(image_name=consensus_image_name,
                                                                               environment=environment,
                                                                               container_name=consensus_node_name,
                                                                               volumes=volumes,
                                                                               exposed_ports=exposed_ports,
                                                                               port_bindings=port_bindings,
                                                                               command=command,
                                                                               working_dir=working_dir))
                tasks.append(task)
            # ------------------------------- (进行共识节点的创建) ----------------------------------
            # ------------------------------- (进行普通节点的创建) ----------------------------------
            number_of_normal_nodes = len(self.normal_nodes)
            for index in range(1, number_of_normal_nodes + 1):
                normal_node_name = f"normal-node{index}"
                normal_node_image_name = self.config_reader.satellite_image_name
                environment = [
                    f"NODE_TYPE=normal_node",
                    f"NODE_ID={index}",
                    f"LISTENING_PORT={self.config_reader.listening_port}"]
                volumes = [
                    f"{self.config_reader.abs_of_frr_configuration}:/configuration/frr"
                ]
                task = asyncio.create_task(self.docker_client.create_container(image_name=normal_node_image_name,
                                                                               environment=environment,
                                                                               container_name=normal_node_name,
                                                                               volumes=volumes))
                tasks.append(task)
            # ------------------------------- (进行普通节点的创建) ----------------------------------
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="create simulation topology")
            for single_task in tasks:
                container_id = single_task.result()
                self.containers[container_id] = cim.ContainerInformation(container_id)
            self.state_of_simulation_topology = SimulationTopology.State.created

    async def start_topology(self):
        """
        进行停止容器的恢复, 只有容器处于 STOPPED 或者 CREATED 的状态的时候才能够被 start 启动起来。
        :return:
        """
        if self.state_of_simulation_topology == SimulationTopology.State.exited or \
                self.state_of_simulation_topology == SimulationTopology.State.created:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(
                    self.docker_client.start_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="start container process ")
            self.state_of_simulation_topology = SimulationTopology.State.running
        else:
            self.my_logger.error("satellite containers not in stopped or created state! could not be started!")
        first_container = list(self.containers.values())[0]
        if not first_container.addr_connect_to_docker_zero:
            await self.inspect_all_nodes_with_id()
        # 进行链接的创建
        await self.generate_connections()

    async def stop_topology(self):
        """
        进行容器的停止 - 只有位于运行状态的容器才能被停止，并将状态转换为停止状态。
        """
        if self.state_of_simulation_topology == SimulationTopology.State.running:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(
                    self.docker_client.stop_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="stop container process  ")
            self.state_of_simulation_topology = SimulationTopology.State.exited
        else:
            self.my_logger.error("satellite containers not in running state! cannot be stopped!")

    async def remove_topology(self):
        """
        进行容器的删除:
            1. 如果容器位于运行状态，那么需要先进行停止，然后进行删除，将状态转换为 NOT_CREATED
            2. 如果容器位于刚创建的状态，那么直接进行删除即可
            3. 如果容器位于停止状态，那么直接进行删除，将状态转换为 NOT_CREATED
        """
        start_time = time.time()
        # 如果容器位于运行状态的处理
        if self.state_of_simulation_topology == SimulationTopology.State.running:
            await self.stop_topology()
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove container process")
            self.containers = {}
            self.name_to_id = {}
            self.state_of_simulation_topology = SimulationTopology.State.not_created
        # 如果容器位于创建状态的处理
        elif self.state_of_simulation_topology == SimulationTopology.State.created:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove container process")
            self.containers = {}
            self.name_to_id = {}
            self.state_of_simulation_topology = SimulationTopology.State.not_created
        # 如果容器位于停止状态的处理
        elif self.state_of_simulation_topology == SimulationTopology.State.exited:
            tasks = []
            for container_id in self.containers.keys():
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove container process")
            self.containers = {}
            self.name_to_id = {}
            self.state_of_simulation_topology = SimulationTopology.State.not_created
        else:
            self.my_logger.error("satellite containers are already be removed!")
            return
        end_time = time.time()
        self.my_logger.info(f"remove time elapsed {end_time - start_time} s")

    async def inspect_all_nodes_without_id(self):
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
        if single_container_info and (self.state_of_simulation_topology == SimulationTopology.State.not_created):
            self.state_of_simulation_topology = SimulationTopology.State[single_container_info["State"]]
        # 然后需要打印现有的卫星的信息
        self.my_logger.success(f"load existing satellites info status {self.state_of_simulation_topology}")
        await self.inspect_all_nodes_with_id()
        self.print_chain_containers_info()

    async def inspect_all_nodes_with_id(self):
        """
        进行卫星网络之中的容器的信息的检查
        """
        if self.state_of_simulation_topology == SimulationTopology.State.not_created:
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
        network_state = len(str(self.state_of_simulation_topology))
        single_part_str = "-" * ((total_length - network_state) // 2)
        print(f"{single_part_str}{self.state_of_simulation_topology}{single_part_str}")
        for container_info in self.containers.values():
            print(container_info)
        print(f"{single_part_str}{self.state_of_simulation_topology}{single_part_str}")

    # ----------------------------- 创建链路相关  -----------------------------

    def bind_container_information(self):
        normal_node_prefix = "normal-node"
        consensus_node_prefix = "consensus-node"
        for node_name in self.name_to_id.keys():
            if node_name.find(normal_node_prefix) != -1:
                # 说明是普通节点
                length = len(normal_node_prefix)
                extract_id = int(node_name[length:])
                container_id = self.name_to_id[node_name]
                container_pid = self.containers[container_id].pid
                normal_node = self.normal_nodes[extract_id - 1]
                normal_node.container_id = container_id
                normal_node.pid = container_pid
            elif node_name.find(consensus_node_prefix) != -1:
                # 说明是共识节点
                # 说明是普通节点
                length = len(consensus_node_prefix)
                extract_id = int(node_name[length:])
                container_id = self.name_to_id[node_name]
                container_pid = self.containers[container_id].pid
                consensus_node = self.consensus_nodes[extract_id - 1]
                consensus_node.container_id = container_id
                consensus_node.pid = container_pid
            else:
                raise ValueError("unrecognized node")
        self.show_all_the_satellites()

    def show_all_the_satellites(self) -> None:
        """
        展示所有的节点
        """
        middle_string = "bind nodes"
        total_length = 97
        length_of_middle_string = len(middle_string)
        single_part_str = "-" * ((total_length - length_of_middle_string) // 2)
        print(f"{single_part_str}{middle_string}{single_part_str}")
        for index, node in enumerate(self.all_nodes):
            print(f"[{index}] {str(node)}")
        print(f"{single_part_str}{middle_string}{single_part_str}")

    # ----------------------------- 创建链路相关  -----------------------------

    async def generate_connections(self):
        """
        进行节点间的连接
        """
        # 首先将网络命名空间放到合适的位置
        dnbm.DockerNamespaceBuilder.build_network_namespace([item.pid for item in self.containers.values()])
        self.bind_container_information()
        await self.generate_veth_pairs_for_all_links()
        # 生成完了之后，根据生成的逻辑星间链路进行实际的 veth 的创建

    async def generate_veth_pairs_for_all_links(self):
        tasks = []
        for link in self.links_without_direction:
            task = asyncio.create_task(self.generate_veth_pair_for_single_link(link))
            tasks.append(task)
        await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="set veth pair process")
        self.tc_settings()

    async def generate_veth_pair_for_single_link(self, inter_satellite_link):
        if inter_satellite_link.source_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
            source_prefix = "nn"
        else:
            source_prefix = "cn"
        if inter_satellite_link.dest_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
            dest_prefix = "nn"
        else:
            dest_prefix = "cn"
        first_veth_name = f"{source_prefix}{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
        first_sat_pid = inter_satellite_link.source_node.pid
        first_sat_ip = inter_satellite_link.source_interface_address
        second_veth_name = f"{dest_prefix}{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
        second_sat_pid = inter_satellite_link.dest_node.pid
        second_sat_ip = inter_satellite_link.dest_interface_address
        command_list = [
            f"sudo ip link add {first_veth_name} type veth peer name {second_veth_name}",
            f"sudo ip link set {first_veth_name} netns {first_sat_pid}",
            f"sudo ip link set {second_veth_name} netns {second_sat_pid}",
            f"sudo ip netns exec {first_sat_pid} ip link set {first_veth_name} up",
            f"sudo ip netns exec {first_sat_pid} ip addr add {first_sat_ip} dev {first_veth_name}",
            f"sudo ip netns exec {second_sat_pid} ip link set {second_veth_name} up",
            f"sudo ip netns exec {second_sat_pid} ip addr add {second_sat_ip} dev {second_veth_name}"
        ]
        for single_command in command_list:
            await raem.RootAuthorityExecutor.async_execute(command=single_command)

    # 进行 tc 的设置
    def tc_settings(self):
        for link in self.links_without_direction:
            if link.source_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
                source_prefix = "nn"
            else:
                source_prefix = "cn"
            if link.dest_node.node_type == nnm.NormalNode.Type.NORMAL_NODE:
                dest_prefix = "nn"
            else:
                dest_prefix = "cn"
            first_veth_name = f"{source_prefix}{link.source_node.node_id}_index{link.source_interface_index + 1}"
            first_sat_pid = link.source_node.pid
            second_veth_name = f"{dest_prefix}{link.dest_node.node_id}_index{link.dest_interface_index + 1}"
            second_sat_pid = link.dest_node.pid
            tc_command_for_veth_first = f"tc qdisc add dev {first_veth_name} root tbf rate 200mbit burst 50mbit latency 1ms"
            tc_command_for_veth_second = f"tc qdisc add dev {second_veth_name} root tbf rate 200mbit burst 50mbit latency 1ms"
            with Namespace(first_sat_pid, "net"):
                os.system(tc_command_for_veth_first)
            with Namespace(second_sat_pid, "net"):
                os.system(tc_command_for_veth_second)

    # ----------------------------- 创建链路相关  -----------------------------

    @classmethod
    def generate(cls):
        """
        进行位置的生成
        """
        start_x = -1
        start_y = 0.3
        x_increase = 0.66
        return {
            "cn1": (start_x, start_y),
            "cn2": (start_x, -start_y),
            "nn1": (start_x + x_increase, 0),
            "nn2": (start_x + 2 * x_increase, 0),
            "cn3": (start_x + 3 * x_increase, start_y),
            "cn4": (start_x + 3 * x_increase, -start_y)
        }

    # ----------------------------- 抓包相关 -----------------------------------
    # def packet_callback(self, packet):
    #     self.total_packet_count += 1
    #     self.total_packet_size += len(packet)

    # def calculate_average_rate(self, finish_queue):
    #     last_total_packet_size = 0
    #     while True:
    #         packet_rate = (self.total_packet_size - last_total_packet_size) / 3 / 1000 / 1000
    #         last_total_packet_size = self.total_packet_size
    #         # 这个计算出来的当前的结果要发送到 flask http 服务器之中
    #         self.deliver_data_to_flask(current_timestamp=time.time(), current_data_rate=packet_rate)
    #         print(f"average packet sending rate: {packet_rate} MBps", flush=True)
    #         time.sleep(3)
    #         if finish_queue.empty():
    #             continue
    #         else:
    #             break
    # ----------------------------- 抓包相关 -----------------------------------

    # ------------------------- 获取 tx rx 相关 --------------------------------
    def deliver_data_to_flask(self, current_timestamp, current_data_rate):
        """
        将当前的时间以及当前的数据传输速率一并发送给flask服务器
        :param current_timestamp: 当前时间戳
        :param current_data_rate: 当前的数据传输速率
        :return:
        """
        url = "http://10.134.148.77:13000/data_add"
        headers = {
            "Content-Type": "application/json"
        }
        json_data = {
            "current_time_stamp": current_timestamp,
            "current_data_rate": current_data_rate
        }
        response = requests.post(url=url, json=json_data, headers=headers)
        if response.status_code == 200:
            print("successful send")
        else:
            print("failure send")

    def get_and_send_real_time_rx_rate(self, interface_name):
        """
        进行指定接口的 rx 速率的获取和发送
        :param interface_name: 要获取的指定的接口
        """
        last_received_bytes = 0
        while True:
            interface = nigm.NetworkInterfacesGetter.get_specified_network_interface(interface_name=interface_name)
            received_bytes = interface["tx"]["bytes"]
            # 进行速率的计算
            data_rate = (received_bytes - last_received_bytes) / 3 / 1000 / 1000
            last_received_bytes = received_bytes
            self.deliver_data_to_flask(current_timestamp=time.time(), current_data_rate=data_rate)
            time.sleep(1)
    # --------------------------获取 tx rx 相关 --------------------------------

    def capture_packet_of_cn_right_first(self):
        """
        进行右上角的节点的接口的抓包
        """
        # 进入某个节点然后进行数据包的抓取
        # 在 root 权限下执行你的代码或命令
        with Namespace(self.consensus_node_right_first.pid, 'net'):
            interface_name = "cn3_index1"
            self.get_and_send_real_time_rx_rate(interface_name=interface_name)
            # finish_queue = Queue()
            # threading.Thread(target=self.calculate_average_rate, args=(finish_queue,)).start()
            # sniff(prn=self.packet_callback, iface=interface_name, count=0)
            # finish_queue.put("finished")
            # 如果 sniff 结束之后就发送一个命令给我们的 thread 让他停止即可。


if __name__ == "__main__":
    simulation_topology_tmp = SimulationTopology(None, None)
    simulation_topology_tmp.plot_graph()
