"""A custom config runner module.

This module is used simple as a playground/testbed for custom configurations of
CyberAttack.

.. warning::

    This module is being deprecated in a future release to make way for
    CyberAttack runner module in the main package.
"""

import os
import sys
import time
from copy import deepcopy
from pathlib import Path
import argparse
import gymnasium as gym

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.ppo import MlpPolicy as PPOMlp

sys.path.append(os.getcwd())
from cyberwheel.envs.cyberwheel_dynamic import DynamicCyberwheel
from cyberwheel.network.network_base import Network
from cyberwheel.agents.red.art_agent import ARTAgent
from cyberwheel.agents.red.strategies import DFSImpact, ServerDowntime


def create_cyberwheel_env(
    network_config: str = "15-host-network.yaml",
    decoy_config: str = "decoy_hosts.yaml",
    host_config: str = "host_definitions.yaml",
    detector_config: str = "example_detector_handler.yaml",
    min_decoys: int = 0,
    max_decoys: int = 1,
    reward_scaling: float = 10.0,
    reward_function: str = "default",
    red_agent: str = "art_agent",
    blue_config: str = "dynamic_blue_agent.yaml",
    num_steps: int = 100,
    red_strategy: str = "server_downtime",
) -> DynamicCyberwheel:
    """Creates a DynamicCyberwheel environment."""

    # Load network from yaml here
    network_config = Path("cyberwheel/resources/configs/network").joinpath(
        network_config
    )
    print(f"Building network: {network_config} ...")
    network = Network.create_network_from_yaml(network_config)

    print("Mapping attack validity to hosts...", end=" ")
    service_mapping = {}
    if red_agent == "art_agent":
        service_mapping = ARTAgent.get_service_map(network)

    if red_strategy == "dfs_impact":
        red_strategy = DFSImpact
    else:
        red_strategy = ServerDowntime

    env: gym.Env = DynamicCyberwheel(
        network_config=network_config,
        decoy_host_file=decoy_config,
        host_def_file=host_config,
        detector_config=detector_config,
        min_decoys=min_decoys,
        max_decoys=max_decoys,
        blue_reward_scaling=reward_scaling,
        reward_function=reward_function,
        red_agent=red_agent,
        blue_config=blue_config,
        num_steps=num_steps,
        network=deepcopy(network),
        service_mapping=service_mapping,
        red_strategy=red_strategy,
    )

    return env


def create_massive_node_env(network_size: int = 10):
    if network_size == 10:
        network_config = "10-host-network.yaml"
    if network_size == 50:
        network_config = "50-host-network.yaml"
    if network_size == 200:
        network_config = "200-host-network.yaml"

    if network_size == 1000:
        network_config = "1000-host-network.yaml"
    if network_size == 5000:
        network_config = "5000-host-network.yaml"
    if network_size == 10000:
        network_config = "10000-host-network.yaml"

    if network_size == 100000:
        network_config = "100000-host-network.yaml"
    if network_size == 150000:
        network_config = "150000-host-network.yaml"

    env = create_cyberwheel_env(network_config)

    return env


def main() -> None:
    """Run the custom config."""
    # Initialize ArgumentParser
    parser = argparse.ArgumentParser(description="Cyber Attack Sim")
    parser.add_argument(
        "--massive_node_size",
        type=int,
        choices=[1000, 5000, 10000, 100000, 150000],
        default=1000,
        help="Number of the massive network node size. Defaults to 1000",
    )
    args = parser.parse_args()

    env = create_massive_node_env(network_size=args.massive_node_size)
    # get the current directory
    current_dir = os.getcwd()
    # directories
    log_dir = os.path.join(current_dir, "work_dir", "massive_nodes_graph")
    tensorboard_log_dir = os.path.join(log_dir, "tf_logs/")
    filename = f"random_connected_graph_{round(time.time())}"
    model_name = os.path.join(log_dir, filename)

    # setup the monitor to check the training
    env = Monitor(env, model_name)
    env.reset()

    agent = PPO(PPOMlp, env, verbose=1, tensorboard_log=tensorboard_log_dir)

    eval_callback = EvalCallback(
        Monitor(env), eval_freq=100, deterministic=False, render=True
    )

    agent.learn(total_timesteps=100000, callback=eval_callback)


if __name__ == "__main__":
    main()
    """_summary_
    """
