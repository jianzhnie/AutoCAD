import importlib
from typing import Iterator, Optional

import matplotlib.pyplot as plt
import networkx as nx
import yaml

from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector


def import_detector(module_name: str,
                    class_name: str,
                    config: Optional[str] = None) -> Detector:
    """Dynamically imports a detector class from a given module and initializes
    it.

    Args:
        module_name (str): The module where the detector class is located.
        class_name (str): The class name of the detector.
        config (Optional[str]): Optional configuration file for the detector.

    Returns:
        Detector: An instance of the detector class.
    """
    import_path = '.'.join(['cyberwheel.detectors.detectors', module_name])
    module = importlib.import_module(import_path)
    detector_class = getattr(module, class_name)
    if config:
        return detector_class(config)
    return detector_class()


class DetectorHandler:

    def __init__(self, config: str) -> None:
        """Initializes the DetectorHandler with a configuration file.

        Args:
            config (str): The file name of the detector handler config file (YAML).
        """
        self.config = config
        self.DG = nx.DiGraph()
        self._from_config()

    def _create_graph(self) -> None:
        """Initializes an empty directed graph for the detector handler."""
        self.DG = nx.DiGraph()

    def _from_config(self) -> None:
        """Parses the configuration file and builds the detector graph."""
        self._create_graph()
        with open(self.config, 'r') as r:
            contents = yaml.safe_load(r)

        adjacency_list = contents['adjacency_list']
        init_info = contents['init_info']

        for entry in adjacency_list:
            node = entry[0]
            detector = None
            self.DG.add_node(node, detector_output=[])
            if node not in ['start', 'end']:
                if node not in init_info:
                    raise KeyError(f'Node {node} not defined in init_info')
                detector = import_detector(
                    init_info[node]['module'],
                    init_info[node]['class'],
                    init_info[node].get('config', None),
                )
            for child in entry[1:]:
                self.DG.add_edge(node, child, attr={'detector': detector})

        # Validate graph structure
        self._validate_graph_structure()

    def _validate_graph_structure(self) -> None:
        """Validates the structure of the detector graph."""
        for node, in_degree in self.DG.in_degree():
            if node == 'start' and in_degree > 0:
                raise ValueError("'start' node must have an in-degree of 0")
            elif node != 'start' and in_degree == 0:
                raise ValueError(f"Node '{node}' must have an in-degree > 0")

        for node, out_degree in self.DG.out_degree():
            if node == 'end' and out_degree > 0:
                raise ValueError("'end' node must have an out-degree of 0")
            elif node != 'end' and out_degree == 0:
                raise ValueError(f"Node '{node}' must have an out-degree > 0")

    def obs(self, perfect_alerts: Iterator[Alert]) -> Iterator[Alert]:
        """Processes alerts through the detector graph.

        Args:
            perfect_alerts (Iterator[Alert]): An iterable of alerts to be processed.

        Returns:
            Iterator[Alert]: Processed alerts that reach the 'end' node.
        """
        for edge in self.DG.edges:
            node_data_view = self.DG.nodes.data('detector_output', default=[])
            next_node_input = node_data_view[edge[1]]
            if edge[0] == 'start':
                result = perfect_alerts
            else:
                input_alerts = node_data_view[edge[0]]
                detector = self.DG.get_edge_data(*edge)['attr']['detector']
                if detector:  # Ensure detector is not None
                    result = detector.obs(input_alerts)
                else:
                    result = input_alerts  # Pass through if no detector

            # Append unique alerts to the next node's input
            for r in result:
                if r not in next_node_input:
                    next_node_input.append(r)
            self.DG.add_node(edge[1], detector_output=next_node_input)

        return self.DG.nodes.data('detector_output', default=[])['end']

    def reset(self) -> None:
        """Resets the detector graph by clearing the detector outputs."""
        for node in self.DG.nodes:
            self.DG.add_node(node, detector_output=[])

    def draw(self, filename: str = 'detector.png') -> None:
        """Draws the detector graph and saves it as an image file.

        Args:
            filename (str): The file to save the drawing of the detector graph to.
        """
        plt.clf()  # Clear any existing plot
        colors = [
            'lightgreen'
            if node == 'start' else 'red' if node == 'end' else 'lightblue'
            for node in self.DG.nodes
        ]
        nx.draw(
            self.DG,
            node_size=300,
            font_size=12,
            font_color='black',
            font_weight='bold',
            edge_color='black',
            with_labels=True,
            node_color=colors,
        )
        plt.savefig(filename)
