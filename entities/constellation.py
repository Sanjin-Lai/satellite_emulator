import json
import sys
import numpy as np

sys.path.append("..")
import asyncio
import copy
import os
import tqdm
import networkx as nx
from entities import satellite as sm
from entities import normal_link as islm
from entities import lir_link_identification as llim
from enum import Enum
from generator import subnet_generator as sgm
from useful_tools import file_operator as fom, work_dir_manager as wdmm
from useful_tools import root_authority_executor as raem
from visualizer import graph_visualizer as gvm
from useful_tools import progress_bar as pbm
from collections import defaultdict

class Constellation:
    class Type(Enum):
        """
        星座的类型：可能为极轨道星座, 可能为倾斜轨道星座
        """
        WALKER_STAR_CONSTELLATION = 1
        WALKER_DELTA_CONSTELLATION = 2

    def __init__(self, orbit_number: int, sat_per_orbit: int, consensus_group_row: int, consensus_group_col: int, constellation_type: Type):
        """
        进行星座的初始化
        :param orbit_number: 轨道的数量
        :param sat_per_orbit: 每轨道的卫星的数量
        :param constellation_type: 星座的类型
        """
        self.orbit_number = orbit_number
        self.sat_per_orbit = sat_per_orbit
        self.consensus_group_row = consensus_group_row
        self.consensus_group_col = consensus_group_col
        self.constellation_type = constellation_type
        self.satellites = []  # 存储在当前星座下的所有的卫星
        self.links_without_direction = []  # 存储无向链路
        self.lir_link_identifiers = []  # lir 的链路标识序列
        self.map_from_source_dest_pair_to_link_identifier = {}
        # 这是一个生成器，为了保证不发生重复，我们只能使用这一个生成器
        self.subnet_generator = sgm.SubnetGenerator.generate_subnets(base_network_tmp="192.168.0.0/16")
        # networkx 产生的有向图
        self.direction_graph = None
        # satellite -> interfaces
        self.node_to_interfaces_map = defaultdict(list)

    def bind_container_information(self, container_name_to_id, containers, node_prefix):
        """
        将逻辑卫星节点和容器id进行绑定
        :param container_name_to_id: 从名称到 id 的一个映射
        :param containers 容器相关信息
        :param node_prefix 节点的前缀
        :return:
        """
        for cm_node_name in container_name_to_id.keys():
            length_of_prefix = len(node_prefix)
            extracted_id = int(cm_node_name[cm_node_name.find(node_prefix) + length_of_prefix:])
            container_id = container_name_to_id[cm_node_name]
            container_pid = containers[container_id].pid
            self.satellites[extracted_id].container_id = container_id
            self.satellites[extracted_id].pid = container_pid
        self.show_all_the_satellites()

    async def generate_veth_pair_for_single_link(self, inter_satellite_link):
        first_veth_name = f"cn{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
        first_sat_pid = inter_satellite_link.source_node.pid
        first_sat_ip = inter_satellite_link.source_interface_address
        second_veth_name = f"cn{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
        second_sat_pid = inter_satellite_link.dest_node.pid
        second_sat_ip = inter_satellite_link.dest_interface_address
        command_list = [
            f"sudo ip link add {first_veth_name} type veth peer name {second_veth_name}",
            f"sudo ip link set {first_veth_name} netns {first_sat_pid}",
            f"sudo ip link set {second_veth_name} netns {second_sat_pid}",
            f"sudo ip netns exec {first_sat_pid} ip link set {first_veth_name} up",
            f"sudo ip netns exec {second_sat_pid} ip link set {second_veth_name} up",
            f"sudo ip netns exec {first_sat_pid} ip addr add {first_sat_ip} dev {first_veth_name}",
            f"sudo ip netns exec {second_sat_pid} ip addr add {second_sat_ip} dev {second_veth_name}"
        ]
        for single_command in command_list:
            await raem.RootAuthorityExecutor.async_execute(command=single_command)

    async def generate_veth_pairs_for_all_links(self, link_cmd_path: str):
        commands = []
        links_dict = dict()
        for inter_satellite_link in self.links_without_direction:
            first_veth_name = f"cn{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
            first_sat_pid = inter_satellite_link.source_node.pid
            first_sat_ip = inter_satellite_link.source_interface_address
            second_veth_name = f"cn{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
            second_sat_pid = inter_satellite_link.dest_node.pid
            second_sat_ip = inter_satellite_link.dest_interface_address
            command_list = [
                f"sudo ip link add {first_veth_name} type veth peer name {second_veth_name}",
                f"sudo ip link set {first_veth_name} netns {first_sat_pid}",
                f"sudo ip link set {second_veth_name} netns {second_sat_pid}",
                f"sudo ip netns exec {first_sat_pid} ip link set {first_veth_name} up",
                f"sudo ip netns exec {second_sat_pid} ip link set {second_veth_name} up",
                f"sudo ip netns exec {first_sat_pid} ip addr add {first_sat_ip} dev {first_veth_name}",
                f"sudo ip netns exec {second_sat_pid} ip addr add {second_sat_ip} dev {second_veth_name}"
            ]
            commands.append(command_list)
        links_dict["linkCommands"] = commands
        with open(link_cmd_path+"/cmd.json", "w", encoding='utf-8') as f:
            json.dump(links_dict, f, indent=2, sort_keys=True, ensure_ascii=False)  # 写为多行

        with wdmm.WorkDirManager(change_dir=link_cmd_path):
            full_command = f"./link start"
            raem.RootAuthorityExecutor.execute(command=full_command)

    # async def generate_veth_pairs_for_all_links(self, link_cmd_path: str):
    #     tasks = []
    #     for inter_satellite_link in self.links_without_direction:
    #         task = asyncio.create_task(self.generate_veth_pair_for_single_link(inter_satellite_link))
    #         tasks.append(task)
    #     await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="set veth pair process")

    def generate_id_to_addresses_mapping(self, generate_destination: str, node_type):
        """
        进行从节点编号到地址的映射的生成
        :param 生成的mapping的文件夹
        :param 节点的类型
        :return: None
        """
        final_str = ""
        for single_satellite in self.satellites:
            line_str = f"{node_type}{single_satellite.node_id}|"
            for item in single_satellite.ip_addresses.items():
                if item[0] != (len(single_satellite.ip_addresses) - 1):
                    line_str += f"{item[1]}|"
                else:
                    line_str += item[1]
            final_str += f"{line_str}\n"
        with open(f"{generate_destination}/address_mapping.conf", "w") as f:
            f.write(final_str)

    def generate_frr_files(self, generate_destination, node_type):
        """
        进行 frr 配置文件的生成
        :param generate_destination: 配置文件生成的地址
        :param node_type: 节点的类型
        :return:
        """
        if not os.path.exists(generate_destination):
            os.system(f"mkdir -p {generate_destination}")
        for single_satellite in self.satellites:
            with open(f"{generate_destination}/"
                      f"{node_type}_{single_satellite.node_id}.conf", "w") as f:
                full_str = \
                    f"""frr version 7.2.1 
frr defaults traditional
hostname satellite_{single_satellite.node_id}
log syslog informational
no ipv6 forwarding
service integrated-vtysh-config
!
router ospf
    redistribute connected
"""
                for connected_subnet in single_satellite.connect_subnet_list:
                    full_str += f"\t network {connected_subnet} area 0.0.0.0\n"

                for interface in self.node_to_interfaces_map[single_satellite.node_id]:
                    full_str += f"interface {interface}\n"
                    full_str += "\t ip ospf network point-to-point\n"
                    full_str += "\t ip ospf area 0.0.0.0\n"
                    full_str += "\t ip ospf hello-interval 10\n"
                    full_str += "\t ip ospf dead-interval 40\n"
                    full_str += "\t ip ospf retransmit-interval 5\n"

                full_str += "!\n"
                full_str += "line vty\n"
                full_str += "!\n"
                f.write(full_str)


    @staticmethod
    async def wait_tasks_with_tqdm(tasks, description=""):
        """
        按照给定的任务进行进度条的生成
        :param tasks:  任务
        :param description: 任务的描述
        :return:
        """
        copied_tasks = copy.copy(tasks)
        task_length = len(copied_tasks)
        bar_format = '{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'
        with tqdm.tqdm(total=task_length, colour="green", ncols=97, postfix="", bar_format=bar_format) as pbar:
            pbar.set_description(description)
            while True:
                done, pending = await asyncio.wait(copied_tasks, return_when=asyncio.FIRST_COMPLETED)
                copied_tasks = list(pending)
                pbar.update(len(done))
                if len(pending) == 0:
                    break

    def generate_satellites(self) -> None:
        """
        生成在星座之中的卫星, 并存放到 self.satellites 列表之中
        """
        for orbit_id in range(0, self.orbit_number):
            for i in range(self.sat_per_orbit * orbit_id, self.sat_per_orbit * (orbit_id + 1)):
                single_satellite = sm.Satellite(i, orbit_id, i % self.sat_per_orbit)
                self.satellites.append(single_satellite)

    def generate_isls_without_direction(self) -> None:
        """
        进行无向星间链路的生成, 并存放到 self.links_without_direction 列表之中
        """
        for single_satellite in self.satellites:
            # ----------------------------------- 进行同轨道星间链路的创建 -----------------------------------
            source_orbit_id = single_satellite.orbit_id
            source_index_in_orbit = single_satellite.index_in_orbit
            source_index = single_satellite.node_id
            source_node = self.satellites[source_index]
            source_interface_index = source_node.interface_index
            dest_orbit_id = source_orbit_id
            dest_index_in_orbit = (source_index_in_orbit + 1) % self.sat_per_orbit
            dest_index = dest_orbit_id * self.sat_per_orbit + dest_index_in_orbit
            dest_node = self.satellites[dest_index]
            dest_interface_index = dest_node.interface_index
            if (source_orbit_id == dest_orbit_id) and (source_index_in_orbit == dest_index_in_orbit):
                pass
            else:
                current_link_id = len(self.links_without_direction)
                # 生成一条无向的星间链路
                # 调用子网生成器进行 ip 的分配
                subnet, first_address, second_address = next(self.subnet_generator)
                source_node.connect_subnet_list.append(subnet)
                dest_node.connect_subnet_list.append(subnet)
                source_node.ip_addresses[source_node.interface_index] = first_address
                dest_node.ip_addresses[dest_node.interface_index] = second_address
                link_tmp = islm.NormalLink(link_id=current_link_id, source_node=source_node,
                                           source_interface_index=source_interface_index,
                                           source_interface_address=first_address,
                                           dest_node=dest_node,
                                           dest_interface_index=dest_interface_index,
                                           link_type=islm.NormalLink.Type.INTRA_ORBIT,
                                           dest_interface_address=second_address)
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                current_link_identification = len(self.lir_link_identifiers)
                forward_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=source_node,
                                                            source_interface_index=source_interface_index,
                                                            dest_node=dest_node)
                source_node.link_identifications[source_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(forward_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (source_node.node_id, dest_node.node_id)] = forward_identifier
                current_link_identification = len(self.lir_link_identifiers)
                reverse_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=dest_node,
                                                            source_interface_index=dest_interface_index,
                                                            dest_node=source_node)
                dest_node.link_identifications[dest_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(reverse_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (dest_node.node_id, source_node.node_id)] = reverse_identifier
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                source_node.interface_index += 1
                dest_node.interface_index += 1
                self.links_without_direction.append(link_tmp)
            # ----------------------------------- 进行同轨道星间链路的创建 -----------------------------------
            # ----------------------------------- 进行异轨道星间链路的创建 -----------------------------------
            dest_orbit_id = source_orbit_id + 1
            if dest_orbit_id < self.orbit_number:
                dest_index_in_orbit = source_index_in_orbit
                dest_index = dest_orbit_id * self.sat_per_orbit + dest_index_in_orbit
                dest_node = self.satellites[dest_index]
                current_link_id = len(self.links_without_direction)
                # 调用子网生成器进行 ip 的分配
                subnet, first_address, second_address = next(self.subnet_generator)
                source_node.connect_subnet_list.append(subnet)
                dest_node.connect_subnet_list.append(subnet)
                source_node.ip_addresses[source_node.interface_index] = first_address
                dest_node.ip_addresses[dest_node.interface_index] = second_address
                link_tmp = islm.NormalLink(link_id=current_link_id, source_node=source_node,
                                           source_interface_index=source_node.interface_index,
                                           source_interface_address=first_address,
                                           dest_node=dest_node,
                                           dest_interface_index=dest_node.interface_index,
                                           dest_interface_address=second_address,
                                           link_type=islm.NormalLink.Type.INTER_ORBIT)
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                current_link_identification = len(self.lir_link_identifiers)
                forward_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=source_node,
                                                            source_interface_index=source_interface_index,
                                                            dest_node=dest_node)
                source_node.link_identifications[source_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(forward_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (source_node.node_id, dest_node.node_id)] = forward_identifier
                current_link_identification = len(self.lir_link_identifiers)
                reverse_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=dest_node,
                                                            source_interface_index=dest_interface_index,
                                                            dest_node=source_node)
                dest_node.link_identifications[dest_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(reverse_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (dest_node.node_id, source_node.node_id)] = reverse_identifier
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                source_node.interface_index += 1
                dest_node.interface_index += 1
                self.links_without_direction.append(link_tmp)
            # ----------------------------------- 进行异轨道星间链路的创建 -----------------------------------
        # ----------------------- 如果是 walker delta 星座还需要额外的一步 [连接首尾轨道] -----------------------
        if self.constellation_type == Constellation.Type.WALKER_DELTA_CONSTELLATION:
            for source_index in range(0, self.sat_per_orbit):
                source_node = self.satellites[source_index]
                source_interface_index = source_node.interface_index
                dest_index = (self.orbit_number - 1) * self.sat_per_orbit + source_index
                dest_node = self.satellites[dest_index]
                dest_interface_index = dest_node.interface_index
                current_link_id = len(self.links_without_direction)
                # 调用子网生成器进行 ip 的分配
                subnet, first_address, second_address = next(self.subnet_generator)
                source_node.connect_subnet_list.append(subnet)
                dest_node.connect_subnet_list.append(subnet)
                source_node.ip_addresses[source_node.interface_index] = first_address
                dest_node.ip_addresses[dest_node.interface_index] = second_address
                link_tmp = islm.NormalLink(link_id=current_link_id,
                                           source_node=source_node,
                                           source_interface_index=source_node.interface_index,
                                           source_interface_address=first_address,
                                           dest_node=dest_node,
                                           dest_interface_index=dest_node.interface_index,
                                           dest_interface_address=second_address,
                                           link_type=islm.NormalLink.Type.INTER_ORBIT)
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                current_link_identificavtion = len(self.lir_link_identifiers)
                forward_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=source_node,
                                                            source_interface_index=source_interface_index,
                                                            dest_node=dest_node)
                source_node.link_identifications[source_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(forward_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (source_node.node_id, dest_node.node_id)] = forward_identifier
                current_link_identification = len(self.lir_link_identifiers)
                reverse_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=dest_node,
                                                            source_interface_index=dest_interface_index,
                                                            dest_node=source_node)
                dest_node.link_identifications[dest_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(reverse_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (dest_node.node_id, source_node.node_id)] = reverse_identifier
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                self.satellites[source_index].interface_index += 1
                self.satellites[dest_index].interface_index += 1
                self.links_without_direction.append(link_tmp)
        # ----------------------- 如果是 walker delta 星座还需要额外的一步 [连接首尾轨道] -----------------------
        self.show_all_the_links_without_direction()

    def record_node_interfaces(self):
        for link in self.links_without_direction:
            first_veth_name = f"cn{link.source_node.node_id}_index{link.source_interface_index + 1}"
            self.node_to_interfaces_map[link.source_node.node_id].append(first_veth_name)
            second_veth_name = f"cn{link.dest_node.node_id}_index{link.dest_interface_index + 1}"
            self.node_to_interfaces_map[link.dest_node.node_id].append(second_veth_name)

    # 进行 chainmaker.yml 的修改
    def modify_nodes_chainmaker_yml(self, path_of_multi_node_config: str):

        """
        修改 multi_node/config/node*/chainmaker.yml 文件
        """
        for satellite in self.satellites:
            new_seeds = []
            full_path_of_chainmaker_yml = f"{path_of_multi_node_config}/node{satellite.node_id + 1}/chainmaker.yml"
            with open(full_path_of_chainmaker_yml, "r") as f:
                full_text = f.read()
            with open(full_path_of_chainmaker_yml, "w") as f:
                start_index = full_text.find("seeds:") + 7
                end_index = full_text.find("# Network tls settings") - 4
                front_part = full_text[:start_index]
                front_part = front_part.replace("listen_addr: /ip4/0.0.0.0/tcp/",
                                                f"listen_addr: /ip4/{satellite.ip_addresses[0][:-3]}/tcp/")
                next_part = full_text[end_index: end_index + 27]
                seeds = full_text[start_index:end_index].split("\n")
                for index, seed in enumerate(seeds):
                    new_seed = seed.replace("127.0.0.1", self.satellites[index].ip_addresses[0][:-3])
                    new_seeds.append(new_seed)
                middle_part = "\n".join(new_seeds)

                # seeds 转化为二维数组
                original_2seeds_array = self.seeds_2array(new_seeds)
                sub_arrays = self.split_array(original_2seeds_array, self.consensus_group_row, self.consensus_group_col)
                sub_group_arrays = self.merge_array(sub_arrays)

                group_part = f'  consensus_groups:\n'
                consensus_group_list = []
                for consensus_group_index, consensus_group_seeds in enumerate(sub_group_arrays):
                    if len(consensus_group_seeds) <= 0:
                        continue
                    consensus_group = f'    - group_id: "{consensus_group_index}"\n'
                    consensus_group += f'      group_seeds:\n'
                    temp_group_seeds = ""
                    for group_seed in consensus_group_seeds:
                        temp_group_seeds += f'    ' + group_seed + "\n"
                    consensus_group += temp_group_seeds
                    consensus_group_list.append(consensus_group)

                end_part = group_part + "".join(consensus_group_list)
                final_text = front_part + middle_part + next_part + "\n" + end_part
                f.write(final_text)
    # 计算共识组
    # -----------------------------------------------------------

    def seeds_2array(self, temp_new_seeds):
        arr1 = np.array(temp_new_seeds)
        arr2 = arr1.reshape((self.sat_per_orbit, self.orbit_number), order='F')
        return arr2.tolist()

    @staticmethod
    def split_array(arr, m, n):
        sub_arrays = []
        rows, cols = len(arr), len(arr[0])
        for i in range(0, rows, m):
            for j in range(0, cols, n):
                sub_array = [arr[x][y] for x in range(i, min(i + m, rows)) for y in range(j, min(j + n, cols))]
                sub_arrays.append(sub_array)
        return sub_arrays

    def merge_array(self, lsts):
        result = []
        current_sublist = []

        for sublst in lsts:
            if len(sublst) < self.consensus_group_col * self.consensus_group_row:
                current_sublist.extend(sublst)
                if len(current_sublist) >= self.consensus_group_col * self.consensus_group_row:
                    result.append(current_sublist)
                    current_sublist = []
            else:
                result.append(sublst)
        # current_sublist 最后一个list是节点数不足consensus_group_col*consensus_group_row的列表，不作为合法的共识组，但仍需记录
        result.append(current_sublist)
        return result

    # 展示相关
    # ------------------------------------------------------------

    def show_all_the_satellites(self) -> None:
        """
        展示所有的卫星
        :return None
        """
        for index, single_satellite in enumerate(self.satellites):
            print(f"[{index}] {str(single_satellite)}")

    def show_all_the_links_without_direction(self) -> None:
        """
        展示所有的无向链路
        :return None
        """
        for single_link_without_direction in self.links_without_direction:
            print(single_link_without_direction)

    def show_all_the_lir_link_identifications(self):
        """
        展示所有的 lir 链路标识
        :return: None
        """
        for single_lir_link_identification in self.lir_link_identifiers:
            print(single_lir_link_identification)

    def calculate_routes_with_all_nodes(self, generate_destination, node_type):
        """
        通过 networkx 计算路由
        :param generate_destination: 生成的地址
        :param node_type: 节点的类型 (sat 或者 consensus_node)
        :return: None
        """
        self.direction_graph = nx.DiGraph()
        node_ids = [single_satellite.node_id for single_satellite in self.satellites]
        # 每一个 entry 是 (start, end ,weight==1)
        link_identifiers = [(single_link_identifier.source_node.node_id, single_link_identifier.dest_node.node_id, 1)
                            for single_link_identifier
                            in self.lir_link_identifiers]
        self.direction_graph.add_nodes_from(node_ids)  # 进行节点的添加
        self.direction_graph.add_weighted_edges_from(link_identifiers)  # 进行链路标识的添加
        for single_node_id in node_ids:
            self.calculate_single_node_routes_to_other(single_node_id, generate_destination, node_type)

    # ------------------------------------------------------------

    def calculate_single_node_routes_to_other(self, current_source_node, generate_destination, node_type):
        """
        生成节点的类型可能是不一样的
        :param current_source_node: 当前节点的编号
        :param generate_destination: 生成的地址
        :param node_type: 节点的类型 (sat 或者 consensus_node)
        :return: None
        """
        all_node_paths = {}
        all_identifier_paths = {}
        node_ids = [single_satellite.node_id for single_satellite in self.satellites]
        for node_id in node_ids:
            if node_id == current_source_node:
                continue
            else:
                path = nx.shortest_path(self.direction_graph, source=current_source_node, target=node_id)
                all_node_paths[node_id] = path

        # convert node path to link identifiers sequence
        for dest_node_id in all_node_paths.keys():
            identifier_path = []
            node_path = all_node_paths[dest_node_id]
            for index in range(len(node_path) - 1):
                source_dest_pair = (node_path[index], node_path[index + 1])
                identifier_path.append(
                    str(self.map_from_source_dest_pair_to_link_identifier[source_dest_pair].link_identification_id))
            all_identifier_paths[dest_node_id] = identifier_path
        final_writing_text = ""
        for dest_node_id in all_identifier_paths.keys():
            sequence = "->".join(all_identifier_paths[dest_node_id])
            single_path_str = f"dest:{dest_node_id} {sequence}\n"
            final_writing_text += single_path_str
        result_file_full_path = f"{generate_destination}/{node_type}_{current_source_node}.conf"
        with open(result_file_full_path, "w") as f:
            f.write(final_writing_text)


def modify_chainmaker_yml_file_test(orbit_num: int, sat_per_orbit: int):
    new_seeds = []
    with open("./chainmaker.yml", "r") as f:
        full_text = f.read()
    with open("./chainmaker.yml", "w") as f:
        start_index = full_text.find("seeds:") + 7
        end_index = full_text.find("# Network tls settings") - 4
        front_part = full_text[:start_index]
        end_part = full_text[end_index:]
        seeds = full_text[start_index:end_index].split("\n")
        for index, seed in enumerate(seeds):
            new_seeds.append(seed)
        group_part = f'  consensus_groups:\n'
        consensus_group_list = []
        for orbit_index in range(orbit_num):
            consensus_group = f'    - group_id: "consensus_group_{orbit_index}"\n'
            consensus_group += f'      node_seeds:\n'
            for node_index in range(orbit_index * sat_per_orbit, (orbit_index + 1) * sat_per_orbit):
                consensus_group += f'    '
                consensus_group += new_seeds[node_index]
                consensus_group += "\n"
            consensus_group_list.append(consensus_group)
        middle_part = "\n".join(new_seeds)
        next_part = group_part + "".join(consensus_group_list)
        final_text = front_part + middle_part + "\n" + next_part + end_part
        f.write(final_text)


if __name__ == "__main__":
    # orbit_number_tmp = 1
    # sat_per_orbit_tmp = 10
    # constellation = Constellation(orbit_number=orbit_number_tmp, sat_per_orbit=sat_per_orbit_tmp,
    #                               constellation_type=Constellation.Type.WALKER_STAR_CONSTELLATION)
    # constellation.generate_satellites()
    # constellation.generate_isls_without_direction()
    # constellation.show_all_the_satellites()
    # constellation.show_all_the_links_without_direction()
    # constellation.show_all_the_lir_link_identifications()
    # constellation.show_all_the_links_without_direction()
    modify_chainmaker_yml_file_test(3, 3)
