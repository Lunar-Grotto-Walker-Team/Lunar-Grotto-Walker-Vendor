# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/Livox-SDK/livox_ros_driver2 |
| 导入分支 | `master` @ `2144554`（CHANGELOG 1.2.8） |
| 导入方式 | `git subtree add --squash` |
| License | MIT / Livox（见 `LICENSE.txt`） |

## 本地改动

### 1. `config/MID360s_config.json` —— 现场网络参数

| 字段 | 上游默认 | 本机 |
|---|---|---|
| `Mid360s.host_net_info[0].host_ip` | `192.168.1.5` | **`192.168.123.18`**（Jetson eth10，driver bind 源） |
| `lidar_configs[0].ip` | `192.168.1.12` | **`192.168.123.20`**（本机 Mid-360S，SN `ARMCP6S0039815`） |

> 换设备/换网段时必须同步改。设备识别、SN↔IP 规则、SDK 版本要求见
> `l4t/ros2_ws/livox_setup.md`。

### 2. 新增两个 launch 文件（非上游）

| 文件 | 用途 |
|---|---|
| `launch_ROS2/msg_MID360s_launch_baselink_launch.py` | 只发点云（CustomMsg），TF 挂 `base_link` 系 |
| `launch_ROS2/rviz_MID360s_launch_baselink_launch.py` | 同上 + RViz |

上游自带的 `msg_MID360s_launch.py` / `rviz_MID360s_launch.py` 用 `livox_frame`，
静态 TF 写死在 launch 里；这两个是按 Go2 的 `base_link` 树改的版本。

## 构建（ROS2 换名是**构建步骤**，产物不入库）

本包上游同时提供 ROS1/ROS2 两套入口，ROS2 编译前必须换名：

```bash
cd src/livox_ros_driver2
rm -f package.xml && cp package_ROS2.xml package.xml
cp -rf launch_ROS2/ launch/
colcon build --packages-select livox_ros_driver2 \
  --cmake-args -DROS_EDITION=ROS2 -DDISTRO_ROS=humble
```

### 为什么不用官方 README 的 `./build.sh humble`

`build.sh` 内部做的就是上面这两步换名（第 61–67 行），换名本身没有冲突。
不能用的原因是它另外三个副作用：

| | `./build.sh humble` | 本文的手动步骤 |
|---|---|---|
| 清理 | `rm -rf ../../build/ ../../devel/ ../../install/`——删掉**整个工作区**的产物 | 不删 |
| 编译范围 | 从 `../../` 跑 `colcon build`，**不带 `--packages-select`** | 只编本包 |
| 收尾 | 编完 `rm -rf launch/` | 保留 |

本仓库 `src/` 下还有 `realsense-ros`、`kindr_ros` 等包，跑 `build.sh` 会把它们
一起拖进无参数编译。

**只有"工作区里只有 livox 一个包"的独立工作区才适合 `build.sh`。**

## 相关文档

- `l4t/ros2_ws/livox_setup.md` —— Mid-360S 设备识别、网络拓扑、SDK 版本、config key 大小写坑
