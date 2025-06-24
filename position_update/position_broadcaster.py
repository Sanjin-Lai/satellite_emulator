from datetime import datetime
import os
import time

import yaml

from loguru import logger
import multiprocessing as mp
from math import cos, sin, sqrt
from pprint import pprint
from nsenter import Namespace
from collections import defaultdict

from satellite_emulator.position_update import global_var as gv
from satellite_emulator.position_update import const_var as cv
from satellite_emulator.position_update import tle_generator as tg


# from position_update import global_var as gv
# from position_update import const_var as cv
# from position_update import tle_generator as tg


def generate_submission_list_for_position_broadcaster(satellite_num, cpu_count):
    if cpu_count < satellite_num:
        # each cpu handle several satellites
        submission_size = (satellite_num // cpu_count) + 1
        submission_list = []
        # [0-2] [3-5] [6-8] [9-9]
        for i in range(0, satellite_num, submission_size):
            if i + submission_size - 1 >= satellite_num:
                submission_list.append((i, satellite_num - 1))
            else:
                submission_list.append((i, i + submission_size - 1))
    else:
        # each satellite is handled by one cpu
        submission_list = [(i, i) for i in range(satellite_num)]
    return submission_list


# stop_process_state, rcv_pipe
def position_broadcast(stop_process_state, rcv_pipe):
    # 等待开始位置更新，否则阻塞
    connection_link = rcv_pipe.recv()
    logger.info("start position and delay update")
    # 读取配置文件
    current_path = os.path.abspath('.')
    config_path = current_path + "/resources/constellation_config.yml"
    with open(config_path) as f:
        content = f.read()
        data = yaml.load(content, Loader=yaml.FullLoader)
        num_of_orbit = data["default"]["num_of_orbit"]
        sat_per_orbit = data["default"]["sat_per_orbit"]
    satellite_nodes, position_datas = tg.generate_tle(num_of_orbit,
                                                      sat_per_orbit,
                                                      0, 0, 0.1, 0.08)
    satellite_num = len(satellite_nodes)
    print(satellite_num)
    gv.satellite_nodes = satellite_nodes[:]
    print("gv.satellite_nodes number: ", len(gv.satellite_nodes))

    # # 打印cpu的数量
    cpu_count = min(mp.cpu_count(), satellite_num)
    logger.info(f"cpu_count: {cpu_count}")
    # 共享数组
    res = mp.Array('f', range(3 * satellite_num), lock=False)
    # 创建进程
    # 创建子任务
    submission_list = generate_submission_list_for_position_broadcaster(satellite_num, cpu_count)
    update_interval = cv.UPDATE_INTERVAL
    init_tc_setting(connection_link)

    while True:
        if stop_process_state.value:
            break
        current_count = 0
        multiple_processes = []
        rcv_pipe_pos, send_pipe_pos = mp.Pipe()
        for i in range(len(submission_list)):
            p = mp.Process(target=tg.worker, args=(submission_list[i][0],
                                                   submission_list[i][1],
                                                   res,
                                                   send_pipe_pos))
            multiple_processes.append(p)
            p.start()

        while True:
            rcv_int = rcv_pipe_pos.recv()
            current_count += rcv_int
            if current_count < satellite_num:
                continue
            else:
                for i in range(satellite_num):
                    node_id_str = "node_" + str(i)
                    index_base = 3 * i
                    position_datas[node_id_str][cv.LATITUDE_KEY] = res[index_base]
                    position_datas[node_id_str][cv.LONGITUDE_KEY] = res[index_base + 1]
                    position_datas[node_id_str][cv.HEIGHT_KEY] = res[index_base + 2]

                # 更新延时
                update_network_delay(position_datas, connection_link)

                for p in multiple_processes:
                    p.kill()
                rcv_pipe_pos.close()
                send_pipe_pos.close()
                break
        time.sleep(update_interval)


def update_network_delay(position_datas, connection_link):
    update_tc_setting_cmd_map = defaultdict(list)
    for link in connection_link:
        first_veth_name = f"cn{link.source_node.node_id}_index{link.source_interface_index + 1}"
        first_sat_pid = link.source_node.pid
        second_veth_name = f"cn{link.dest_node.node_id}_index{link.dest_interface_index + 1}"
        second_sat_pid = link.dest_node.pid

        # 用于获取对应节点的位置
        source_id_str = "node_" + str(link.source_node.node_id)
        dest_id_str = "node_" + str(link.dest_node.node_id)
        delay = get_laser_delay_ms(position_datas[source_id_str], position_datas[dest_id_str])

        tc_command_for_veth_first = "tc qdisc replace dev %s %s netem delay %dms loss %s rate %s" % (
            first_veth_name, "root", delay, cv.NETWORK_LOSS, cv.NETWORK_BANDWIDTH)
        tc_command_for_veth_second = "tc qdisc replace dev %s %s netem delay %dms loss %s rate %s" % (
            second_veth_name, "root", delay, cv.NETWORK_LOSS, cv.NETWORK_BANDWIDTH)

        update_tc_setting_cmd_map[first_sat_pid].append(tc_command_for_veth_first)
        update_tc_setting_cmd_map[second_sat_pid].append(tc_command_for_veth_second)

    for sat_pid, cmd_list in update_tc_setting_cmd_map.items():
        with Namespace(sat_pid, "net"):
            for cmd in cmd_list:
                os.system(cmd)


def init_tc_setting(connection_link):
    init_cmd_map = defaultdict(list)
    for link in connection_link:
        first_veth_name = f"cn{link.source_node.node_id}_index{link.source_interface_index + 1}"
        first_sat_pid = link.source_node.pid
        second_veth_name = f"cn{link.dest_node.node_id}_index{link.dest_interface_index + 1}"
        second_sat_pid = link.dest_node.pid

        tc_command_for_veth_first = "tc qdisc add dev %s %s netem delay %dms loss %s rate %s" % (
            first_veth_name, "root", cv.NETWORK_DELAY, cv.NETWORK_LOSS, cv.NETWORK_BANDWIDTH)
        tc_command_for_veth_second = "tc qdisc add dev %s %s netem delay %dms loss %s rate %s" % (
            second_veth_name, "root", cv.NETWORK_DELAY, cv.NETWORK_LOSS, cv.NETWORK_BANDWIDTH)

        init_cmd_map[first_sat_pid].append(tc_command_for_veth_first)
        init_cmd_map[second_sat_pid].append(tc_command_for_veth_second)

    for sat_pid, cmd_list in init_cmd_map.items():
        with Namespace(sat_pid, "net"):
            for cmd in cmd_list:
                os.system(cmd)


def get_laser_delay_ms(position1: dict, position2: dict) -> int:
    lat1, lon1, hei1 = position1[cv.LATITUDE_KEY], position1[cv.LONGITUDE_KEY], position1[cv.HEIGHT_KEY] + cv.R_EARTH
    lat2, lon2, hei2 = position2[cv.LATITUDE_KEY], position2[cv.LONGITUDE_KEY], position2[cv.HEIGHT_KEY] + cv.R_EARTH
    x1, y1, z1 = hei1 * cos(lat1) * cos(lon1), hei1 * cos(lat1) * sin(lon1), hei1 * sin(lat1)
    x2, y2, z2 = hei2 * cos(lat2) * cos(lon2), hei2 * cos(lat2) * sin(lon2), hei2 * sin(lat2)
    dist_square = (x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2  # UNIT: m^2
    # logger.info(f"distance: {int(sqrt(dist_square))} light speed: {LIGHT_SPEED}")
    return int(sqrt(dist_square) / cv.LIGHT_SPEED)


if __name__ == "__main__":
    # position_broadcaster()
    print(gv.satellite_nodes)
