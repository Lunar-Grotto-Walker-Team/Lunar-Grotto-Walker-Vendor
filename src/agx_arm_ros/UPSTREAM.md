# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/agilexrobotics/agx_arm_ros |
| 导入版本 | 分支 `ros2` @ `b9ad14d`（2026-09-04） |
| 导入方式 | `git subtree add -P src/agx_arm_ros b9ad14d --squash` |
| License | MIT（见 `LICENSE`，版权声明为上游原样 `Copyright (c) 2026 aalicecc`） |
| 包 | `agx_arm_ctrl`（驱动）、`agx_arm_description`、`agx_arm_moveit`、`agx_arm_msgs` |

## 子模块处理（`src/agx_arm_description/agx_arm_urdf`）

上游把它声明为子模块（`agilexrobotics/agx_arm_urdf`），内容包括 URDF/xacro 文本
与约 **205 MB 的 meshes**。按本仓库收录规则，未改动的大体积上游不入库：

- 导入时移除了 `.gitmodules` 与该路径的 gitlink；
- 版本固定在根目录 `deps.agx-arm-urdf.repos`（commit `f6642ce`，即 `b9ad14d` 记录的 gitlink）；
- 部署时执行：

```bash
vcs import src/agx_arm_ros/src/agx_arm_description < deps.agx-arm-urdf.repos
```

> ⚠️ `agx_arm_description/CMakeLists.txt` 会 `install(DIRECTORY agx_arm_urdf ...)`，
> **没有先导入这个子模块，`colcon build` 会在该包失败**。
> 另外，日后 `git subtree pull` 上游时 gitlink 会重新出现，需要再次 `git rm --cached`
> 并确认 `.gitmodules` 未被带回。

## 本地改动

### 1. `agx_arm_moveit/config/initial_positions.yaml`、
`agx_arm_moveit/config/agx_arm.srdf`、`agx_arm_moveit/config/agx_arm.srdf.xacro`
与 `agx_arm_ctrl/agx_arm_ctrl/agx_arm_ctrl_single_node.py` —— park 位姿替代全零

**症状**：起栈或调用 `/move_home` 后机械臂 j3 顶在限位，固件进入保护/失能，
腕部靠重力落下。

**根因**：`joint3` 的 0 正好是 URDF 限位上限（`[-2.967, 0]`）。上游在
`initial_positions` 与 `move_home` 里都下发全零。

**修法**：home 位姿改为 `j2=0.30, j3=-0.20`，三处配置与驱动的 `/move_home` 保持一致。

### 2. `agx_arm_moveit/config/agx_arm.urdf.xacro`、
`agx_arm_moveit/config/agx_arm.ros2_control.xacro`、
`agx_arm_moveit/launch/_moveit_config_builder.py`、`demo.launch.py` —— topic 硬件后端

新增 `hardware_backend:=fake|topic`（默认 `fake`，行为不变）：

- `fake`：`mock_components/GenericSystem`（上游原样）；
- `topic`：`agx_topic_hardware/AgxTopicSystem`，state 取 `/feedback/joint_states`，
  command 写 `/control/joint_states`；
- `topic` 下 JSB（joint_state_broadcaster）重映射到 `/joint_states`——否则它会把初始状态
  先于第一帧真实反馈灌给驱动，实测把手臂从 park 拉到 j3 限位；
- `topic` 下 `arm_controller` 增加 `open_loop_control: true` 与轨迹容差：真机跟随有
  ~0.3 s 滞后，JTC 默认的零容差会中止正常轨迹。

> `agx_topic_hardware` 是团队自写包，位于主仓库，不在本仓库。

### 3. `agx_arm_moveit/launch/rsp.launch.py` —— TF 帧前缀

`robot_state_publisher` 的 `/tf`、`/tf_static` 是绝对话题，namespace 不会改帧名；
新增 `frame_prefix` 参数（为空时由 `namespace` 派生），避免多臂时
`base_link → link1` 互相覆盖。

### 4. `test/gripper/test_gripper_joint_states.yaml`

采样值调整：`position 0.05 → 0.0`，`effort 1.0 → 2.0`。

## 运行时依赖

| 依赖 | 方式 | 说明 |
|---|---|---|
| `pyAgxArm` | `pip install -e <pyAgxArm>`（或 `pip install pyAgxArm`） | `agx_arm_ctrl` 的 CAN SDK，**不在本仓库** |
| MoveIt 2 | apt `ros-humble-moveit*` | `agx_arm_moveit` 依赖 |
| CAN | `can_activate.sh can0 1000000` | 1 Mbps，机械臂驱动前置 |

## 构建

```bash
# 1) 先按 §子模块处理 导入 agx_arm_urdf
# 2) 再编译
colcon build --symlink-install --packages-select \
  agx_arm_msgs agx_arm_ctrl agx_arm_description agx_arm_moveit
```

## 相关文档

- 原改动与回退记录：`l4t/lg_walker_ws/docs/dev/2026-11-06-vendor-modifications-and-rollback.md`
- 引入模式：`docs/third-party-modes.md`
- 第三方索引：根目录 `NOTICE`
