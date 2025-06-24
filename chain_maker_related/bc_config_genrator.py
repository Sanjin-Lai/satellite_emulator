class bc_config_generator:
    def __init__(self, output_dir_path: str, node_count: int):
        """
        进行 bcx.yml 配置文件的初始化
        :param output_dir_path: 产出的 bcx.yml 的存放位置
        :param node_count: 要生成的节点的数量
        """
        self.output_dir_path = output_dir_path
        self.front_part_of_bc_file = "resources/front_part_of_bc_file"
        self.back_part_of_bc_file = "resources/back_part_of_bc_file"
        self.node_count = node_count

    def generate(self):
        """
        进行 bc 配置文件的产生
        :return:
        """
        final_output = ""
        # -------------- 添加前面的部分的内容 ---------------
        with open(self.front_part_of_bc_file) as f:
            front_content = f.read()
        final_output += front_content
        # -------------- 添加前面的部分的内容 ---------------
        # ------------- 添加动态变化的部分的内容 -------------
        consensus_part_and_trust_roots = f"""
# Consensus settings
consensus:
  # Consensus type
  # 0-SOLO, 1-TBFT, 3-MAXBFT, 4-RAFT, 5-DPOS, 6-ABFT
  type: {{consensus_type}}

  # Consensus node list
  nodes:
    # Each org has one or more consensus nodes.
    # We use p2p node id to represent nodes here.
    
"""
        for index in range(1, self.node_count+1):
            consensus_part_and_trust_roots += f'    - org_id: "{{org{index}_id}}"\n'
            consensus_part_and_trust_roots += f'      node_id:\n'
            consensus_part_and_trust_roots += f'        - "{{org{index}_peerid}}"\n'

        consensus_part_and_trust_roots += f"""
  # We can specify other consensus config here in key-value format.
  ext_config:
    # - key: aa
    #   value: chain01_ext11
    
# Trust roots is used to specify the organizations' root certificates in permessionedWithCert mode.
# When in permessionedWithKey mode or public mode, it represents the admin users.
trust_roots:
  # org id and root file path list.

"""
        for index in range(1, self.node_count+1):
            consensus_part_and_trust_roots += f'  - org_id: "{{org{index}_id}}"\n'
            consensus_part_and_trust_roots += f'    root:\n'
            consensus_part_and_trust_roots += f'      - "../config/{{org_path}}/certs/ca/{{org{index}_id}}/ca.crt"\n'
        final_output += consensus_part_and_trust_roots
        # ------------- 添加动态变化的部分的内容 -------------
        # -------------- 添加后面的部分的内容 ---------------
        with open(self.back_part_of_bc_file) as f:
            back_content = f.read()
        final_output += back_content
        # -------------- 添加后面的部分的内容 ---------------
        output_file_name = f"{self.output_dir_path}/bc_{self.node_count}.tpl"
        with open(output_file_name, "w") as f:
            f.write(final_output)
