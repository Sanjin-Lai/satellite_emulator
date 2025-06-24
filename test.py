import json

first_veth_name = "veth1"
second_veth_name = "veth2"

first_sat_pid = "pid1"
first_sat_ip = "ip1"

second_sat_pid = "pid2"
second_sat_ip = "ip2"

my_dict = dict()

command_list = [
    f"sudo ip link add {first_veth_name} type veth peer name {second_veth_name}",
    f"sudo ip link set {first_veth_name} netns {first_sat_pid}",
    f"sudo ip link set {second_veth_name} netns {second_sat_pid}",
    f"sudo ip netns exec {first_sat_pid} ip link set {first_veth_name} up",
    f"sudo ip netns exec {second_sat_pid} ip link set {second_veth_name} up",
    f"sudo ip netns exec {first_sat_pid} ip addr add {first_sat_ip} dev {first_veth_name}",
    f"sudo ip netns exec {second_sat_pid} ip addr add {second_sat_ip} dev {second_veth_name}"
]

commands = list()
commands.append(command_list)
commands.append(command_list)

my_dict["linkCommands"] = commands


with open("write_json.json", "w", encoding='utf-8') as f:
    json.dump(my_dict, f, indent=2, sort_keys=True, ensure_ascii=False)  # 写为多行

