import asyncio
import multiprocessing
import sys
import time
from multiprocessing import Pipe
from ctypes import c_bool

import PyInquirer
import pexpect as px
import os
from interact import questions as qm
from config import config_reader as crm
from useful_tools import file_operator as fom, work_dir_manager as wdmm
from useful_tools import logger as lm
from useful_tools import root_authority_executor as raem
from generator import leo_or_chain_generator as cgm
from chain_maker_related import bc_config_genrator as bcgm


class UserInterfaceForLeoOrChain:
    def __init__(self):
        """
        进行链创建用户界面的初始化
        """
        self.config_reader = crm.ConfigReader()
        self.my_logger = lm.Logger().get_logger()
        self.bc_config_generator = None
        self.answers_for_chain_maker = None
        self.answers_for_continue = None
        self.answers_for_delete = None
        # lai xin
        self.answers_for_config_selection = None
        self.answers_for_chain_maker_config = None

    def start(self):
        """
        进行用户参数的获取然后调用 prepare.sh
        """

        self.regenerate_config_files()
        self.chain_maker_management()

    # lai xin
    def delete_logs(self):
        full_command = f"sudo true > {self.config_reader.abs_of_multi_node}/log/log*/system.log "
        raem.RootAuthorityExecutor.execute(command=full_command)

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
        # lai xin
        # 重新生成配置文件
        # 首先进行判断是否进行删除
        self.answers_for_delete = PyInquirer.prompt(qm.CHAIN_MAKER_CONFIG_DELETE_QUESTION)
        if self.answers_for_delete["command"] == "yes":
            delete_dirs = [
                f"{self.config_reader.abs_of_multi_node}/log",
                f"{self.config_reader.abs_of_multi_node}/config",
                f"{self.config_reader.abs_of_multi_node}/data",
            ]
            full_command = "sudo rm -rf"
            for single_delete_dir in delete_dirs:
                full_command += f" {single_delete_dir}"
            raem.RootAuthorityExecutor.execute(command=full_command)
            self.generate_certs_ymlconfig(full_path=self.config_reader.abs_of_node_config_generator,
                                          consensus_protocol_type=self.config_reader.consensus_protocol_type,
                                          p2p_port=self.config_reader.p2p_port,
                                          rpc_port=self.config_reader.rpc_port)
            # self.change_ip_address()
        else:
            delete_dirs = [
                f"{self.config_reader.abs_of_multi_node}/log",
                f"{self.config_reader.abs_of_multi_node}/data",
            ]
            full_command = "sudo rm -rf"
            for single_delete_dir in delete_dirs:
                full_command += f" {single_delete_dir}"
            raem.RootAuthorityExecutor.execute(command=full_command)

    # def generate_bc_config(self):
    #     """
    #     进行 bcx.tpl 的产生, 是运行 prepare.sh 的前提, 所以 generate_bc_config 一定要在 call_prepare_sh 之前进行运行
    #     """
    #     self.bc_config_generator = bcgm.bc_config_generator(output_dir_path=self.config_reader.abs_of_chainconfig,
    #                                                         node_count=self.config_reader.number_of_cm_node)
    #     self.bc_config_generator.generate()

    # def call_prepare_sh(self, full_path: str, node_count: int, p2p_port: int, rpc_port: int):
    #     """
    #     通过 prepare.sh 的绝对路径进行 prepare.sh 的调用
    #     :param full_path: prepare.sh 的绝对路径
    #     :param node_count: 要生成的共识节点的数量和后面的 chainmaker-go/scripts/docker/multi_node/create_docker_compose_yml.sh 为总的节点的数量
    #     :param p2p_port: p2p 的端口
    #     :param rpc_port: rpc 的端口
    #     :return:
    #     """
    #     self.my_logger.info("start to generate config of different nodes")
    #     chain_count = 1  # 默认只有一条链
    #     dir_path = os.path.dirname(full_path)
    #     file_name = os.path.basename(full_path)
    #     with wdmm.WorkDirManager(change_dir=dir_path):
    #         full_command = f"./{file_name} {node_count} {chain_count} {p2p_port} {rpc_port} "
    #         process = px.spawn(full_command, encoding="utf-8", timeout=600)
    #         process.logfile_read = sys.stdout
    #         process.expect(".*:")
    #         process.sendline("1")  # ( 1-TBFT, 3-MAXBFT, 4-RAFT)
    #         process.expect(".*:")
    #         process.sendline("INFO")  # (DEBUG|INFO(DEFAULT)|WARN|ERROR)
    #         process.expect(".*:")
    #         process.sendline("NO")  # enable vm go (YES|NO(default))
    #         process.expect(px.EOF)

    def generate_certs_ymlconfig(self, full_path: str, consensus_protocol_type: int, p2p_port: int, rpc_port: int):
        self.my_logger.info("start to generate config of different nodes")
        # full_path 为snc所在目录
        with wdmm.WorkDirManager(change_dir=full_path):
            full_command = f"./snc generate -c {consensus_protocol_type} -p {p2p_port} -r {rpc_port}"
            raem.RootAuthorityExecutor.execute(command=full_command)
            self.my_logger.info("Satellite certs and ymlConfigs generated successfully!")

            protocol_type = ""
            if consensus_protocol_type == 0:
                protocol_type = "PBFT"
            elif consensus_protocol_type == 1:
                protocol_type = "H-PBFT"
            elif consensus_protocol_type == 2:
                protocol_type = "T-PBFT"
            self.my_logger.info(f"Consensus protocol: {protocol_type}")

    def change_ip_address(self):
        """
        需要进行 ip 的改变
        :return:
        """
        with wdmm.WorkDirManager(change_dir=self.config_reader.abs_of_multi_node):
            ip_address = "10.134.180.145"
            os.system(f"""sed -i "s%127.0.0.1%{ip_address}%g" config/node*/chainmaker.yml""")

    def get_user_choice(self):
        self.answers_for_chain_maker = PyInquirer.prompt(qm.CHAIN_MAKER_RELATED_QUESTION)

    def continue_or_not(self):
        """
        是否继续进行管理
        :return:
        """
        self.answers_for_continue = PyInquirer.prompt(qm.PROGRAM_CONTINUE_QUESTION)

    def chain_maker_management(self):
        """
        进行长安链的管理, 包括容器的创建，启动，停止，删除
        :return:
        """
        chain_generator = cgm.LeoOrChainGenerator(config_reader=self.config_reader, my_logger=self.my_logger)
        asyncio.run(chain_generator.inspect_chain_without_id())
        # used for position update
        rcv_pipe, send_pipe = Pipe()
        stop_process_state = multiprocessing.Value(c_bool, False)
        position_update_obj = cgm.LeoOrChainGenerator.SatellitePosition(stop_process_state, rcv_pipe)
        while True:
            try:
                self.get_user_choice()
                command = self.answers_for_chain_maker["command"]
                if command == "create":
                    asyncio.run(chain_generator.create_chain())
                elif command == "start":
                    asyncio.run(chain_generator.start_chain())
                elif command == "stop":
                    try:
                        stop_process_state.value = True
                        position_update_obj.stop_update_process()
                    except:
                        pass
                    finally:
                        asyncio.run(chain_generator.stop_chain())
                elif command == "remove":
                    # lai xin 更新容器位置的进程结束
                    try:
                        stop_process_state.value = True
                        position_update_obj.stop_update_process()
                    except Exception as e:
                        pass
                    finally:
                        rcv_pipe.close()
                        send_pipe.close()
                        asyncio.run(chain_generator.remove_chain())
                elif command == "inspect":
                    asyncio.run(chain_generator.inspect_chain_without_id())
                # lai xin
                elif command == "position_update":
                    stop_process_state.value = False
                    position_update_obj.start_update_process()
                    temp_list = chain_generator.logical_constellation.links_without_direction[:]
                    send_pipe.send(temp_list)
                elif command == "delete_logs":
                    # 清除logs 保存新一轮共识的结果
                    self.delete_logs()
                else:
                    raise ValueError("command should be create | stop | remove | "
                                     "continue | inspect | ")
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
