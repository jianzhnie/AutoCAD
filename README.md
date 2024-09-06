# CyberAttackSimulator

## Table of Content

- [CyberAttackSimulator](#cyberattacksimulator)
  - [Table of Content](#table-of-content)
  - [About CyberAttackSimulator](#about-cyberattacksimulator)
  - [Getting Started](#getting-started)
  - [Usage](#usage)
  - [CyberAttackSimulator GUI](#cyberattacksimulator-gui)
    - [CyberAttackSimulator GUI 是如何构建的](#cyberattacksimulator-gui-是如何构建的)
    - [启动 GUI](#启动-gui)
  - [使用 Docker](#使用-docker)
    - [Build Docker](#build-docker)
      - [For CUDA users](#for-cuda-users)
      - [For Ascend NPU users](#for-ascend-npu-users)
    - [在 NPU 上启动 Docker 须知](#在-npu-上启动-docker-须知)
    - [关于当前镜像](#关于当前镜像)
  - [代码规范](#代码规范)
    - [步骤 1: 安装 `pre-commit`](#步骤-1-安装-pre-commit)
    - [步骤 2: 创建 `.pre-commit-config.yaml` 配置文件](#步骤-2-创建-pre-commit-configyaml-配置文件)
    - [步骤 3: 安装 `pre-commit` 钩子](#步骤-3-安装-pre-commit-钩子)
    - [步骤 4: 手动运行 `pre-commit` 钩子](#步骤-4-手动运行-pre-commit-钩子)
  - [License](#license)
  - [Acknowledgements](#acknowledgements)
  - [Citation](#citation)

## About CyberAttackSimulator

CyberAttackSimulator 是一组抽象的、高度灵活的基于图形的强化学习 (RL) 网络安全模拟环境, 用于在模拟网络上训练和评估自主网络防御模型, 提供了标准的基于 OpenAI Gym 强化学习环境接口。它在构建时考虑到了模块化，以便用户可以根据自己的需求在其基础上进行构建。它支持各种强大的配置文件来构建网络、服务、主机类型、防御代理等。

**动机**

- 可在高度可定制的配置中防御任意网络拓扑结构。
- 可扩展性——允许修改和添加各种防御行动和进攻策略，而无需对代码库进行结构性更改。
- 可扩展性——以最小的性能成本支持大型网络的训练

**设计原则**

CyberAttackSimulator 的设计遵循了以下关键原则：

- 简单胜过复杂
- 最低硬件要求
- 操作系统无关
- 支持多种算法
- 增强智能体/策略评估
- 支持灵活的环境和游戏规则配置

## Getting Started

为了安装 CyberAttackSimulator，您需要安装以下软件：

- python3.10
- python3-pip
- nvirtualenv

CyberAttackSimulator 的设计与操作系统无关，因此应该适用于 Linux、Windows 和 MacOS 的大多数版本/发行版。该项目在 Python 3.10 上运行并已通过测试。

1. 创建并激活虚拟环境

```shell
conda create -n cybersim python=3.10 && conda activate cybersim
```

2. 克隆源代码

使用 HTTPS 克隆 CyberAttackSimulator 仓库

```shell
git clone https://git.pcl.ac.cn/niejzh/CyberAttackSimulator.git
```

3. 安装所有依赖项：

```shell
cd CyberAttackSimulator
pip install -r requirements.txt
```

## Usage

要运行任何 CyberAttackSimulator 脚本，请进入 `cybersim` 虚拟环境. 所有运行的例子都在 `examples` 文件夹下。

1. `随机节点数量网络` 环境创建，模型训练, 这里，你可以尝试不同的网络结构和修改网络节点数量。

```python
python examples/cyberattacksim/run_random_nodes_env.py
```

2. `随机连接网络` 环境创建，模型训练

```python
python cyber/CyberAttackSimulator/examples/cyberattacksim/run_random_connected_graph_env.py
```

3. 运行一个 18 节点网络自动攻防（DQN， A2C， PPO）

```python
python examples/cyberattacksim/run_default_18_nodes_env.py --algo_name dqn --env_id default_18_node_network
python examples/cyberattacksim/run_default_18_nodes_env.py --algo_name a2c --env_id default_18_node_network
python examples/cyberattacksim/run_default_18_nodes_env.py --algo_name ppo --env_id default_18_node_network
```

## CyberAttackSimulator GUI

### CyberAttackSimulator GUI 是如何构建的

CyberAttackSimulator GUI 是作为底层 CyberAttackSimulator 库的可选扩展而设计的。CyberAttackSimulator GUI 主要使用Django将 CyberAttackSimulator 的各个方面转换为 html 对象，用户可以在本地浏览器实例中与这些对象进行交互，从而允许执行底层 Python，而无需命令行界面或 Python 语言知识。

CyberAttackSimulator GUI 还集成了定制版Cytoscape JS ，该版本已扩展为可直接与 CyberAttackSimulator 配合使用。这允许用户直接与网络拓扑交互并编辑网络节点的位置和属性，从而主动更新存储网络的数据库。

### 启动 GUI

如果您是一位对 CyberAttackSimulator 进行更改的开发人员，则可以从克隆的 repo 运行 GUI 来测试您的更改：

```python
python3 -m manage.py runserver
```

## 使用 Docker

### Build Docker

#### For CUDA users

- Build Docker

```shell
docker build -f ./docker/docker-cuda/Dockerfile \
    --build-arg INSTALL_BNB=false \
    --build-arg INSTALL_VLLM=false \
    --build-arg INSTALL_DEEPSPEED=false \
    --build-arg INSTALL_FLASHATTN=false \
    --build-arg PIP_INDEX=https://pypi.org/simple \
    -t cybersim:latest .
```

- Start the Docker daemon

```shell
docker run -dit --gpus=all \
    -v ./hf_cache:/root/.cache/huggingface \
    -v ./ms_cache:/root/.cache/modelscope \
    -v ./data:/app/data \
    -v ./output:/app/output \
    -p 7860:7860 \
    -p 8000:8000 \
    --shm-size 16G \
    --name cybersim \
    cybersim:latest
```

- Exec command to step inside a running Docker container

```shell
docker exec -it cybersim:latest bash
```

#### For Ascend NPU users

- Build Docker

```shell
# Choose docker image upon your environment
docker build -f ./docker/docker-npu/Dockerfile \
    --build-arg INSTALL_DEEPSPEED=false \
    --build-arg PIP_INDEX=https://pypi.org/simple \
    -t cybersim:latest .
```

- Start the Docker daemon

```shell
# Change `device` upon your resources
docker_images=cybersim:latest
model_dir=/path_to/CyberAttackSimulator
docker run -it -u root --ipc=host --net=host \
        --device=/dev/davinci0 \
        --device=/dev/davinci_manager \
        --device=/dev/devmm_svm \
        --device=/dev/hisi_hdc \
        -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
        -v /usr/local/Ascend/add-ons/:/usr/local/Ascend/add-ons/ \
        -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
        -v ${model_dir}:${model_dir} \
        -v /var/log/npu:/usr/slog ${docker_images} \
        /bin/bash
```

- Exec command to step inside a running Docker container

```shell
docker exec -it cybersim:latest bash
```

- Stop & Kill a Running Docker Container

```shell
docker stop container_id
docker kill container_id
```

### 在 NPU 上启动 Docker 须知

注意启动 Docker 容器时：

- `--device=/dev/davinci0` 是将第`0`张卡挂载到容器里面；

- 挂载多张卡时， 可以这样添加：

- `--device=/dev/davinci0`

- `--device=/dev/davinci1`

- `model_dir` 需要挂载到容器使用的代码目录， 如果需要挂载其他路径，可以参考这种方式

- 当前的卡挂载到容器时是以独占的方式， 所以如果启动 Docker 时尽量选择一张空的卡

### 关于当前镜像

- CANN版本：8.0

- 操作系统版本：Ubuntu18.08

- 昇腾驱动固件版本：23.0.0以上

- Python版本：3.10.13

- 几个关键 Python 包版本

  ```shell
  gymnasium==0.29.1
  networkx==3.3
  pandas==2.2.2
  stable_baselines3==2.3.2
  tinydb==4.7.0
  torch==2.2
  Django==5.1
  django-cors-headers==4.4.0
  ```

## 代码规范

项目使用 `pre-commit` 来对代码格式进行统一。 `pre-commit` 是一个用于在提交代码之前自动运行代码检查和格式化工具的框架。它能帮助开发者确保代码在提交前符合一定的标准，减少代码审查的工作量和代码库中的问题。以下是一个详细的 `pre-commit` 教程。

### 步骤 1: 安装 `pre-commit`

首先，你需要安装 `pre-commit`。你可以使用 `pip` 来安装：

```
pip install pre-commit
```

### 步骤 2: 创建 `.pre-commit-config.yaml` 配置文件

在你的项目根目录下创建一个 `.pre-commit-config.yaml` 文件。这是 `pre-commit` 的配置文件，用于定义需要运行的钩子（hooks）。

这里 `.pre-commit-config.yaml` 已经定义好了，无需编辑，跳过这一步。

### 步骤 3: 安装 `pre-commit` 钩子

在配置文件创建并保存后，运行以下命令来安装 `pre-commit` 钩子：

```shell
pre-commit install
```

这将会在 `.git/hooks` 目录中安装 `pre-commit` 钩子，每次你运行 `git commit` 时，这些钩子都会自动执行。

### 步骤 4: 手动运行 `pre-commit` 钩子

在你进行第一次提交前，你可以手动运行所有文件的 `pre-commit` 钩子来确保没有问题：

```shell
pre-commit run --all-files
```

这将对所有文件执行配置文件中定义的钩子。

```shell
pre-commit run ---file path_to_your_code
```

这将对某个特定的文件执行配置文件中定义的钩子。

## License

`CyberAttackSimulator` is released under the Apache 2.0 license.

## Acknowledgements

We appreciate the work by many open-source contributors, especially:

- [Yawning Titan](https://github.com/dstl/YAWNING-TITAN)
- [CyberBattleSim](https://github.com/microsoft/CyberBattleSim)
- [CybORG](https://github.com/cage-challenge/CybORG)
- [NetworkAttackSimulator](https://github.com/Jjschwartz/NetworkAttackSimulator)

## Citation

Please cite the repo if you use the data or code in this repo.

```bibtex
@misc{CyberAttackSimulator,
  author = {jianzhnie},
  title = {Auto Cybersecurity Simulator: A reinforcement learning simulation environment focused on autonomous cyber defence.},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/jianzhnie/CyberAttackSimulator}},
}
```
