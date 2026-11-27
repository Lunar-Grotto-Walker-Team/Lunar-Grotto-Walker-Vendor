# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/unitreerobotics/unitree_ros2 |
| 导入版本 | 附注 tag `v0.3.0`（tag 对象 `12c080c`，指向 commit `66ae098`） |
| 导入方式 | `git subtree add --squash` |
| License | BSD-3-Clause（见 `LICENSE`） |

## 本地改动

### `setup.sh` —— 从 foxy 默认值改为本机 Humble + eth10

| 项 | 上游 | 本机 |
|---|---|---|
| ROS 发行版 | `/opt/ros/foxy/setup.bash` | **`/opt/ros/humble/setup.bash`** |
| install 路径 | `$HOME/unitree_ros2/...` | **脚本自身目录**（`BASH_SOURCE` 推导，仓库可放任意位置） |
| 网卡 | `enp3s0` | **`eth10`**（Go2 内部网络，`/utlidar/*`、`/lf/sportmodestate` 从这里来） |
| `AllowMulticast` | 默认（等价 true） | **`spdp`** |
| `MaxAutoParticipantIndex` | 默认 | **`30`** |

**`AllowMulticast=spdp` 是最关键的一条**：默认允许用户数据走组播，同一大话题只要
≥2 个订阅者，同机进程间的数据也要从 `eth10` 出去再绕回来，有效吞吐仅 ~12 MB/s——
13.5 MB 的 `/aft_pgo_map` 每帧 publish 要 1.1 s，订阅端只收到 0.6 Hz。
`spdp` 表示只有发现阶段用组播、数据一律单播，同机单播由内核路由到 `lo`，
publish 回到 ~32 ms（2026-11-12 实测）。

两个反例（**不要**这么做）：

- `AllowMulticast=false` —— 连 SPDP 一起关掉，对端发现不了；
- 把 `lo` 加进接口列表 —— Cyclone 0.10.5 会选 `lo` 做组播接口并全局禁用组播，
  `/utlidar/*` 整路消失（121 → 2 个话题）。

### 未改动的部分

`cyclonedds_ws/`（`unitree_go`、`unitree_api` 消息包）与上游 v0.3.0 **逐字节一致**。

## 构建

```bash
cd src/unitree_ros2/cyclonedds_ws
colcon build
```

之后用仓库根的 `setup.sh`（它会 source `cyclonedds_ws/install/setup.bash`）。
