# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/Livox-SDK/livox_ros_driver2 |
| 导入分支 | `master` |
| 导入 commit | `2144554`（2026-11-26 导入时 HEAD，CHANGELOG 版本 1.2.8） |
| 导入方式 | `git subtree add --squash` |
| License | MIT / Livox（见 `LICENSE.txt`） |

## 本地改动

### 1. `config/MID360s_config.json` —— 现场网络参数

| 字段 | 上游默认 | 本机 |
|---|---|---|
| `Mid360s.host_net_info[0].host_ip` | `192.168.1.5` | **`192.168.123.18`**（Jetson eth10，driver bind 源） |
| `lidar_configs[0].ip` | `192.168.1.12` | **`192.168.123.20`**（本机 Mid-360S 改后 IP，SN `ARMCP6S0039815`） |

其余字段（含 `extrinsic_parameter`）保持上游默认。

> 这是**现场网络参数**，换设备/换网段时必须同步改。设备识别、SN↔IP 规则、
> SDK 版本要求见 `l4t/ros2_ws/livox_setup.md`。

### 2. 新增两个 launch 文件（非上游）

| 文件 | 用途 |
|---|---|
| `launch_ROS2/msg_MID360s_launch_baselink_launch.py` | 只发点云（CustomMsg），TF 挂到 `base_link` 系 |
| `launch_ROS2/rviz_MID360s_launch_baselink_launch.py` | 同上 + RViz |

上游自带的 `msg_MID360s_launch.py` / `rviz_MID360s_launch.py` 用的是 `livox_frame`
且静态 TF 写死在 launch 里；这两个文件是我们按 Go2 的 `base_link` 树改的版本。

> ⚠️ 这两个文件放在 vendor 目录里，是为了让驱动包自包含。
> 如果以后要严格遵循"自写代码只放主仓库"的约定，可以把它们迁到主仓库的
> bringup 包里（`subtree pull` 不会删除它们，但会与新上游文件混在一起）。

## 构建注意（**不是**源码改动，不要提交）

本包上游同时提供 ROS1/ROS2 两套入口，ROS2 编译前必须做一次换名：

```bash
cd src/livox_ros_driver2
rm -f package.xml && cp package_ROS2.xml package.xml
cp -rf launch_ROS2/ launch/
colcon build --packages-select livox_ros_driver2 \
  --cmake-args -DROS_EDITION=ROS2 -DDISTRO_ROS=humble
```

`package.xml` 和 `launch/` 是构建步骤产物，**不纳入版本控制**——
它们由上面两条命令生成，`subtree pull` 后重新执行即可。

## 相关文档

- `l4t/ros2_ws/livox_setup.md` —— Mid-360S 设备识别、网络拓扑、SDK 版本、config key 大小写坑
