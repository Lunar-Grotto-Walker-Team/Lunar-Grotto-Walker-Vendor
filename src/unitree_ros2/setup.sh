#!/bin/bash
# Unitree ROS2 环境 + CycloneDDS 配置。
#
# 相对上游的改动见同目录 UPSTREAM.md。这里把 install 路径改成脚本自身位置，
# 使仓库可以克隆到任意目录（上游硬编码 $HOME/unitree_ros2）。
source /opt/ros/humble/setup.bash
_UNITREE_ROS2_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$_UNITREE_ROS2_DIR/cyclonedds_ws/install/setup.bash"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Interfaces: 只列 eth10（狗的内部网络，/utlidar/*、/lf/sportmodestate 等
# 外部节点只能从这里看到）。
#
# AllowMulticast=spdp 是这个文件里最要紧的一行（Cyclone 默认等价于 true）：
# 默认允许用户数据走组播，同一个大话题只要有 **≥2 个订阅者**，同机进程间的
# 数据就从 eth10 出去再绕回来，有效吞吐只有 ~12 MB/s —— 13.5 MB 的
# /aft_pgo_map 每帧 publish 要 ~1.1 s，订阅端只收到 ~0.6 Hz。
# spdp = 只有发现阶段用组播，数据一律单播；同机单播包由内核路由到 lo，
# publish 回到 ~32 ms。2026-11-12 实测（2 读者、13.5 MB、1 Hz）：
#   AllowMulticast=true  1153.9 ms，eth10 TX +98 MB、lo +0
#   AllowMulticast=spdp    32.5 ms，eth10 TX  +0、   lo +246 MB
# 发现不受影响：spdp 仍然用组播，121 个话题（含 18 个 /utlidar/*）、
# /utlidar/robot_pose 正常收数。
#
# 不要用 AllowMulticast=false（连 SPDP 一起关，对端发现不了）；
# 也不要往接口列表里加 lo（Cyclone 0.10.5 会选 lo 做组播接口并全局禁用组播，
# /utlidar/* 整路消失，121 → 2）。
#
# MaxAutoParticipantIndex: Cyclone picks a participant index by binding the
# RTPS unicast ports of that index. Measured 2026-11-12 (while the list also
# contained `lo`, i.e. two interfaces): 15 concurrent participants -> only
# 8-9 succeeded with the default range, 15/15 with the limit raised to 30; a
# stock MoveIt stack peaks at 10 and failed at launch with "Failed to find a
# free participant index for domain 0". `lo` is gone now so the pressure is
# lower, but the raised limit is harmless and kept.
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces>
                            <NetworkInterface name="eth10" priority="default" multicast="default" />
                        </Interfaces><AllowMulticast>spdp</AllowMulticast></General>
                        <Discovery><MaxAutoParticipantIndex>30</MaxAutoParticipantIndex></Discovery>
                    </Domain></CycloneDDS>'
