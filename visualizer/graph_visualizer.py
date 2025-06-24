from enum import Enum
import matplotlib.pyplot as plt
import networkx as nx
from visualizer import constellation_layout as clm
from attack import simulation_topology as stm


class GraphVisualizer:
    class Type(Enum):
        CONSTELLATION = 1
        TEST_TOPOLOGY = 2
        OTHER_TOPOLOGY = 3

    @classmethod
    def plot_graph(cls, nodes, edges, topology_type,
                   orbit_number=None, sat_per_orbit=None, node_colors=None, node_size=None,
                   legend_handles=None):
        """
        进行图的绘制
        :param nodes: 节点的列表
        :param edges: 边的列表，每一条边的格式为 (源节点, 目的节点)
        :param topology_type: 要绘制的图的拓扑类型
        :param orbit_number: (可选参数) 轨道的数量
        :param sat_per_orbit: (可选参数) 每个轨道卫星的数量
        :param node_colors: 节点的颜色列表,
        :param node_size: 节点的大小
        :param legend_handles: 图例
        """
        plt.figure(figsize=(5, 1.5), dpi=500)
        graph_temp = nx.Graph()
        graph_temp.add_nodes_from(nodes)
        graph_temp.add_edges_from(edges)
        if topology_type == GraphVisualizer.Type.CONSTELLATION:
            if not all([orbit_number, sat_per_orbit]):
                raise ValueError("you need to specify the orbit_number and sat_per_orbit")
            position = clm.ConstellationLayout.generate(orbit_number=orbit_number, sat_per_orbit=sat_per_orbit)
        elif topology_type == GraphVisualizer.Type.TEST_TOPOLOGY:
            position = stm.SimulationTopology.generate()
        else:
            position = nx.shell_layout(G=graph_temp)
        if node_colors is None:
            nx.draw(G=graph_temp, pos=position, with_labels=True, node_color="blue",
                    font_color="white", node_shape="s", node_size=node_size)
        else:
            nx.draw(G=graph_temp, pos=position, with_labels=True, node_color=node_colors,
                    font_color="white", node_shape="s", node_size=node_size)
        if legend_handles is not None:
            plt.legend(handles=legend_handles, loc="upper center")
        else:
            pass
        plt.show()


if __name__ == "__main__":
    nodes_tmp = ['0', '1', '2', '3', '4', '5', 'a', 'b', 'c']
    edges_tmp = [('0', '1'), ('2', '3')]
    GraphVisualizer.plot_graph(nodes=nodes_tmp, edges=edges_tmp, topology_type=GraphVisualizer.Type.OTHER_TOPOLOGY)
