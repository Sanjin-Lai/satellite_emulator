import json
import os
import time
import random
import string

from useful_tools import work_dir_manager as wdmm
from loguru import logger


class ContractRelatedCommand:
    CONTRACT_CREATION_COMMAND = r'''client contract user create --contract-name=fact --runtime-type=WASMER --byte-code-path=./testdata/claim-wasm-demo/rust-fact-2.0.0.wasm --version=1.0 --sdk-conf-path=./testdata/sdk_config.yml --admin-key-file-paths=./testdata/crypto-config/wx-org1.chainmaker.org/user/admin1/admin1.sign.key,./testdata/crypto-config/wx-org2.chainmaker.org/user/admin1/admin1.sign.key,./testdata/crypto-config/wx-org3.chainmaker.org/user/admin1/admin1.sign.key --admin-crt-file-paths=./testdata/crypto-config/wx-org1.chainmaker.org/user/admin1/admin1.sign.crt,./testdata/crypto-config/wx-org2.chainmaker.org/user/admin1/admin1.sign.crt,./testdata/crypto-config/wx-org3.chainmaker.org/user/admin1/admin1.sign.crt --sync-result=true --params="{}"'''

    CONTRACT_INVOCATION_COMMAND = r"""client contract user invoke --contract-name=fact --method=save --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_name\":\"name007\",\"file_hash\":\"ab3456df5799b87c77e7f88\",\"time\":\"6543234\"}" --sync-result=true"""

    CONTRACT_SEARCH_COMMAND = r'''client contract user get --contract-name=fact --method=find_by_file_hash --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_hash\":\"ab3456df5799b87c77e7f88\"}"'''


class ContractManager:
    def __init__(self, cmc_exe_dir: str, my_logger: logger):
        """
        进行 contractManager 的初始化
        :param cmc_exe_dir: cmc 可执行文件所在目录的绝对路径
        :param my_logger: 日志
        """
        self.cmc_exe_dir = cmc_exe_dir
        self.my_logger = my_logger
        self.invoke_commands = list()
        self.invoke_commands_params = list()
        self.search_commands = list()

    def create_contract(self):
        """
        调用 cmc 可执行文件进行合约的创建
        """
        # 这是一个上下文管理器，在 with 块之中的工作目录被切换为 self.config_reader.abs_of_cmc_dir
        with wdmm.WorkDirManager(change_dir=self.cmc_exe_dir):
            # execute command
            print(os.getcwd())
            print(f"./cmc {ContractRelatedCommand.CONTRACT_CREATION_COMMAND}")
            r = os.popen(f"./cmc {ContractRelatedCommand.CONTRACT_CREATION_COMMAND}")
            text = r.read()
            r.close()
            self.my_logger.success(text)

    def create_invoke_cmds(self):
        self.invoke_commands = list()  # 保存新生成的Invoke命令
        self.invoke_commands_params = list()  # 保存新生成的file_hash，用于查询使用
        for i in range(10):
            new_file_name = "name" + ''.join(random.sample(string.digits, 3))
            new_file_hash = ''.join(random.sample(string.ascii_letters + string.digits, 23))
            new_time = ''.join(random.sample(string.digits, 7))
            self.invoke_commands_params.append(new_file_hash)
            original_cmd = r"""client contract user invoke --contract-name=fact --method=save --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_name\":\"name014\",\"file_hash\":\"ab3456df5799b87c77e7f95\",\"time\":\"6543241\"}" --sync-result=true"""
            new_cmd = original_cmd.replace("name014", new_file_name)
            new_cmd = new_cmd.replace("ab3456df5799b87c77e7f95", new_file_hash)
            new_cmd = new_cmd.replace("6543241", new_time)
            self.invoke_commands.append(new_cmd)

        # self.invoke_commands = list()
        # original_cmd = r"""client contract user invoke --contract-name=fact --method=save --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_name\":\"name014\",\"file_hash\":\"ab3456df5799b87c77e7f95\",\"time\":\"6543241\"}" --sync-result=true"""
        # self.invoke_commands.append(original_cmd)

    def invoke_contract(self):
        """
        调用 cmc 可执行文件进行合约的调用
        """
        # 这是一个上下文管理器，在 with 块之中的工作目录被切换为 self.config_reader.abs_of_cmc_dir
        with wdmm.WorkDirManager(change_dir=self.cmc_exe_dir):
            # execute command
            # print(f"./cmc {ContractRelatedCommand.CONTRACT_INVOCATION_COMMAND}")
            # r = os.popen(f"./cmc {ContractRelatedCommand.CONTRACT_INVOCATION_COMMAND}")
            # text = r.read()
            # r.close()
            # self.my_logger.success(text)
            # for cmd in ContractRelatedCommand.CONTRACT_INVOCATION_COMMAND:
            for cmd in self.invoke_commands:
                print(f"./cmc {cmd}")
                r = os.popen(f"./cmc {cmd}")
                result = json.loads(r.read())
                r.close()
                self.my_logger.success("block chain height: " + str(result["tx_block_height"]))
                time.sleep(3)

    def search_contract(self):
        """
        调用 cmc 可执行文件进行合约的查询
        """
        # 这是一个上下文管理器，在 with 块之中的工作目录被切换为 self.config_reader.abs_of_cmc_dir
        self.search_commands = list()
        original_cmd = r'''client contract user get --contract-name=fact --method=find_by_file_hash --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_hash\":\"ab3456df5799b87c77e7f88\"}"'''
        for file_hash in self.invoke_commands_params:
            new_cmd = original_cmd.replace("ab3456df5799b87c77e7f88", file_hash)
            self.search_commands.append(new_cmd)
        for search_cmd in self.search_commands:
            with wdmm.WorkDirManager(change_dir=self.cmc_exe_dir):
                # execute command
                r = os.popen(f"./cmc {search_cmd}")
                text = r.read()
                r.close()
                self.my_logger.success(text)
                time.sleep(3)
