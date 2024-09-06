from typing import Dict

import yaml


def read_detector_yaml(filename: str) -> Dict[str, float]:
    """Helper function to read a YAML configuration file containing detection
    probabilities for various techniques.

    Args:
        filename (str): The path to the YAML file.

    Returns:
        Dict[str, float]: A dictionary mapping techniques to their detection
        probabilities.
    """
    with open(filename, 'r') as yaml_file:
        techniques = yaml.safe_load(yaml_file)
    return techniques
