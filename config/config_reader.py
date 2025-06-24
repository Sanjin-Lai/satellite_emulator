import yaml


class ConfigReader:

    def __init__(self, *params):
        """
        能实现多参数重载
        :param params: 传入的参数
        :exception TypeError
        """
        self.num_of_orbit = None
        self.sat_per_orbit = None

        self.consensus_group_row = None
        self.consensus_group_col = None
        self.consensus_protocol_type = None
        self.max_generated_subnet = None
        self.base_network_address = None
        self.satellite_image_name = None
        self.ground_image_name = None
        # 计算卫星数量
        self.number_of_satellites = None
        self.base_url = None
        self.listening_port = None
        # self.docker_cpu_limit = None
        self.access_image_name = None

        self.abs_of_node_config_generator = None
        self.abs_of_multi_node = None
        # lai xin
        self.abs_of_existed_chainmaker_config = None
        # resources/constellation_config.yml
        self.abs_of_constellation_config = None
        self.abs_of_links_generator = None

        self.abs_of_frr_configuration = None
        self.abs_of_routes_configuration = None
        self.abs_of_address_configuration = None

        self.p2p_port = None
        self.rpc_port = None
        self.signal_port = None

        self.topology_cn_node = None
        self.generate_leo_or_chain = None

        if len(params) <= 2:
            self.load(*params)
        else:
            raise TypeError(f"accept parameters 0 1 2, however {len(params)} params are given")

    def load(self, configuration_file_path: str = "resources/constellation_config.yml",
             selected_config: str = "default"):
        """
        进行配置文件的加载
        :param configuration_file_path 配置文件的路径
        :param selected_config 选择的配置
        :exception yaml.parser.ParserError | ValueError | TypeError
        :return:
        """
        with open(file=configuration_file_path, mode='r', encoding="utf-8") as f:
            selected_config_data = yaml.load(stream=f, Loader=yaml.FullLoader).get(selected_config, None)
        if selected_config_data is not None:
            self.num_of_orbit = int(selected_config_data.get("num_of_orbit", None))
            self.sat_per_orbit = int(selected_config_data.get("sat_per_orbit", None))
            self.consensus_group_row = int(selected_config_data.get("consensus_group_row", None))
            self.consensus_group_col = int(selected_config_data.get("consensus_group_col", None))
            self.consensus_protocol_type = int(selected_config_data.get("consensus_protocol_type", None))

            self.max_generated_subnet = int(selected_config_data.get("max_generated_subnet", None))
            self.base_network_address = selected_config_data.get("base_network_address", None)
            self.satellite_image_name = selected_config_data.get("satellite_image_name", None)
            self.ground_image_name = selected_config_data.get("ground_image_name", None)
            # 计算卫星数量
            self.number_of_satellites = self.num_of_orbit * self.sat_per_orbit
            self.base_url = selected_config_data.get("base_url", None)
            self.listening_port = int(selected_config_data.get("listening_port", None))
            # self.docker_cpu_limit = int(selected_config_data.get("docker_cpu_limit", None))
            self.access_image_name = selected_config_data.get("access_image_name", None)

            self.abs_of_node_config_generator = selected_config_data.get("abs_of_node_config_generator", None)
            self.abs_of_multi_node = selected_config_data.get("abs_of_multi_node", None)

            self.abs_of_existed_chainmaker_config = selected_config_data.get("abs_of_existed_nodes_config", None)
            self.abs_of_constellation_config = selected_config_data.get("abs_of_constellation_config", None)
            self.abs_of_links_generator = selected_config_data.get("abs_of_links_generator", None)

            self.abs_of_frr_configuration = selected_config_data.get("abs_of_frr_configuration", None)
            self.abs_of_routes_configuration = selected_config_data.get("abs_of_routes_configuration", None)
            self.abs_of_address_configuration = selected_config_data.get("abs_of_address_configuration", None)

            self.p2p_port = int(selected_config_data.get("p2p_port", None))
            self.rpc_port = int(selected_config_data.get("rpc_port", None))
            self.signal_port = int(selected_config_data.get("signal_port", None))

            self.topology_cn_node = int(selected_config_data.get("topology_cn_node", None))
            self.generate_leo_or_chain = selected_config_data.get("generate_leo_or_chain", None)

            if not all([self.num_of_orbit, self.sat_per_orbit,
                        self.consensus_group_row, self.consensus_group_col,
                        self.max_generated_subnet, self.base_network_address,
                        self.satellite_image_name, self.ground_image_name,
                        self.number_of_satellites, self.base_url, self.listening_port,
                        # self.docker_cpu_limit,
                        self.access_image_name, self.abs_of_node_config_generator,
                        self.abs_of_multi_node, self.abs_of_existed_chainmaker_config,
                        self.abs_of_constellation_config, self.abs_of_frr_configuration,
                        self.abs_of_routes_configuration, self.abs_of_address_configuration,
                        self.p2p_port, self.rpc_port, self.topology_cn_node, self.generate_leo_or_chain]):
                raise ValueError(f"not all parameter get its value: {str(self)}")
        else:
            raise ValueError(f'cannot find selected config "{selected_config}"')

    def __str__(self):
        """
        :return: 配置对象的字符串表示
        """
        format_str = f"""
        -----------------[configuration]----------------
        num_of_orbit: {self.num_of_orbit}
        sat_per_orbit: {self.sat_per_orbit}
        consensus_group_row: {self.consensus_group_row}
        consensus_group_col: {self.consensus_group_col}
        consensus_protocol_type: {self.consensus_protocol_type}
        
        max_generated_subnet: {self.max_generated_subnet}
        base_network_address: {self.base_network_address}
        satellite_image_name: {self.satellite_image_name}
        ground_image_name: {self.ground_image_name}
        number_of_satellites: {self.number_of_satellites}
        base_url: {self.base_url}
        listening_port: {self.listening_port}
        access_image_name: {self.access_image_name}
        
        abs_of_node_config_generator: {self.abs_of_node_config_generator}
        abs_of_multi_node: {self.abs_of_multi_node}
        abs_of_existed_chainmaker_config: {self.abs_of_existed_chainmaker_config}
        abs_of_constellation_config: {self.abs_of_constellation_config}
        
        abs_of_frr_configuration: {self.abs_of_frr_configuration}
        abs_of_routes_configuration: {self.abs_of_routes_configuration}
        abs_of_address_configuration: {self.abs_of_address_configuration}
        p2p_port: {self.p2p_port}
        rpc_port: {self.rpc_port}
        
        topology_cn_node: {self.topology_cn_node}
        generate_leo_or_chain: {self.generate_leo_or_chain}
        -----------------[configuration]----------------
        """
        return format_str


if __name__ == "__main__":
    docker_client_config = ConfigReader("../resources/constellation_config.yml")
    print(docker_client_config)
