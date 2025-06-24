import asyncio
import os
import sys
import PyInquirer
import pexpect as px
from config import config_reader as crm
from useful_tools import logger as lm
from interact import questions as qm
from attack import simulation_topology as stm
from useful_tools import root_authority_executor as raem
from chain_maker_related import bc_config_genrator as bcgm
from useful_tools import file_operator as fom, work_dir_manager as wdmm
from command_client import command_client_unit as ccum


class UserInterfaceForSimulationTopology:
    def __init__(self):
        """
        进行模拟拓扑用户界面的初始化
        """
        self.config_reader = crm.ConfigReader()
        self.my_logger = lm.Logger().get_logger()
        self.bc_config_generator = None
        self.answers_for_chain_maker = None
        self.answers_for_continue = None
        self.answers_for_delete = None

    def start(self):
        """
        进行用户参数的获取然后调用 prepare.sh
        """
        self.regenerate_config_files()
        self.simulation_topology_management()

    def regenerate_config_files(self):
        """
        进行产生的文件的删除
        第一个要删除的文件夹：{multi_node/log}
        第二个要删除的文件夹: {multi_node/data}
        第三个要删除的文件夹: {multi_node/config}
        第四个要删除的文件夹: {chainmaker-go/tools/cmc/testdata/crypto-config}
        既然删除了就需要进行重新的配置文件的产生
        :return:
        """
        # 首先进行判断是否进行删除
        self.answers_for_delete = PyInquirer.prompt(qm.CHAIN_MAKER_CONFIG_DELETE_QUESTION)
        if self.answers_for_delete["command"] == "yes":
            delete_dirs = [
                f"{self.config_reader.abs_of_frr_configuration}/*",
                f"{self.config_reader.abs_of_multi_node}/log",
                f"{self.config_reader.abs_of_multi_node}/data",
                f"{self.config_reader.abs_of_multi_node}/config",
                f"{self.config_reader.abs_of_testdata}/crypto-config"
            ]

            full_command = "sudo rm -rf"
            for single_delete_dir in delete_dirs:
                full_command += f" {single_delete_dir}"
            raem.RootAuthorityExecutor.execute(command=full_command)
            self.generate_bc_config()
            self.call_prepare_sh(full_path=self.config_reader.abs_of_prepare,
                                 node_count=self.config_reader.topology_cn_node,
                                 p2p_port=self.config_reader.p2p_port,
                                 rpc_port=self.config_reader.rpc_port)
            self.copy_crypto_config()
            self.copy_build_config()
            self.change_ip_address()
        else:
            pass

    def generate_bc_config(self):
        """
        进行 bcx.tpl 的产生, 是运行 prepare.sh 的前提, 所以 generate_bc_config 一定要在 call_prepare_sh 之前进行运行
        """
        self.bc_config_generator = bcgm.bc_config_generator(output_dir_path=self.config_reader.abs_of_chainconfig,
                                                            node_count=self.config_reader.number_of_cm_node)
        self.bc_config_generator.generate()

    def call_prepare_sh(self, full_path: str, node_count: int, p2p_port: int, rpc_port: int):
        """
        通过 prepare.sh 的绝对路径进行 prepare.sh 的调用
        :param full_path: prepare.sh 的绝对路径
        :param node_count: 要生成的共识节点的数量和后面的 chainmaker-go/scripts/docker/multi_node/create_docker_compose_yml.sh 为总的节点的数量
        :param p2p_port: p2p 的端口
        :param rpc_port: rpc 的端口
        :return:
        """
        self.my_logger.info("start to generate config of different nodes")
        chain_count = 1  # 默认只有一条链
        dir_path = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        with wdmm.WorkDirManager(change_dir=dir_path):
            full_command = f"./{file_name} {node_count} {chain_count} {p2p_port} {rpc_port} "
            process = px.spawn(full_command, encoding="utf-8")
            process.logfile_read = sys.stdout
            process.expect(".*:")
            process.sendline("1")  # ( 1-TBFT, 3-MAXBFT, 4-RAFT)
            process.expect(".*:")
            process.sendline("DEBUG")  # (DEBUG|INFO(DEFAULT)|WARN|ERROR)
            process.expect(".*:")
            process.sendline("NO")  # enable vm go (YES|NO(default))
            process.expect(px.EOF)

    def copy_crypto_config(self):
        """
        将 crypto-config 拷贝到 testdata 之中从而方便进行后续的测试
        :return:
        """
        self.my_logger.info("copy crypto-config to testdata")
        fom.FileOperator.copy_dir(self.config_reader.abs_of_crypto_config, self.config_reader.abs_of_testdata)

    def copy_build_config(self):
        """
        将 build/config 之中总的内容拷贝到 scripts/docker/multi_node 目录之中
        :return:
        """
        self.my_logger.info("copy build/config to scripts/docker/multi_node")
        fom.FileOperator.copy_dir(self.config_reader.abs_of_build_config, self.config_reader.abs_of_multi_node)

    def change_ip_address(self):
        """
        需要进行 ip 的改变
        :return:
        """
        with wdmm.WorkDirManager(change_dir=self.config_reader.abs_of_multi_node):
            ip_address = "10.134.148.77"
            os.system(f"""sed -i "s%127.0.0.1%{ip_address}%g" config/node*/chainmaker.yml""")

    def get_user_choice(self):
        self.answers_for_chain_maker = PyInquirer.prompt(qm.CHAIN_MAKER_RELATED_QUESTION)

    def continue_or_not(self):
        """
        是否继续进行管理
        :return:
        """
        self.answers_for_continue = PyInquirer.prompt(qm.PROGRAM_CONTINUE_QUESTION)

    def simulation_topology_management(self):
        """
        进行长安链的管理, 包括容器的创建，启动，停止，删除
        :return:
        """
        topology_manager = stm.SimulationTopology(config_reader=self.config_reader, my_logger=self.my_logger)
        asyncio.run(topology_manager.inspect_all_nodes_without_id())
        while True:
            try:
                self.get_user_choice()
                command = self.answers_for_chain_maker["command"]
                if command == "create":
                    asyncio.run(topology_manager.create_topology())
                elif command == "start":
                    asyncio.run(topology_manager.start_topology())
                elif command == "stop":
                    asyncio.run(topology_manager.stop_topology())
                elif command == "remove":
                    asyncio.run(topology_manager.remove_topology())
                elif command == "inspect":
                    asyncio.run(topology_manager.inspect_all_nodes_without_id())
                elif command == "send":
                    if not topology_manager.state_of_simulation_topology == stm.SimulationTopology.State.running:
                        self.my_logger.error("cannot send msg to chain when they are not in running state!")
                    else:
                        command_client = ccum.CommandClientUnit(server_listen_port=self.config_reader.listening_port,
                                                                name_to_id=topology_manager.name_to_id,
                                                                containers=topology_manager.containers,
                                                                logger=self.my_logger,
                                                                available_name_prefix="normal-node")
                        command_client.interact_with_user()
                elif command == "capture":
                    topology_manager.capture_packet_of_cn_right_first()
                elif command == "create_contract":
                    topology_manager.contract_manager.create_contract()
                elif command == "invoke_contract":
                    topology_manager.contract_manager.invoke_contract()
                elif command == "search_contract":
                    topology_manager.contract_manager.search_contract()
                else:
                    raise ValueError("command should be create | stop | remove | "
                                     "continue | inspect | create_contract | "
                                     "invoke_contract | search_contract")
                self.continue_or_not()
                continue_program = self.answers_for_continue["continue"]
                if continue_program == "yes":
                    continue
                else:
                    break
            except Exception as e:
                print(e)
                self.continue_or_not()
                continue_program = self.answers_for_continue["continue"]
                if continue_program == "yes":
                    continue
                else:
                    break
