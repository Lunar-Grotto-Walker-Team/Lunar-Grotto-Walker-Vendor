# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/SivertHavso/kindr_ros |
| 导入分支 | `galactic` @ `af5667c`（`elevation_mapping` README 指定的分支） |
| 导入方式 | `git subtree add --squash` |
| License | BSD-3-Clause（见 `LICENSE`） |

包含 4 个包：`kindr_msgs`、`kindr_ros`、`kindr_rviz_plugins`、
`multi_dof_joint_trajectory_rviz_plugins`。

## 本地改动

### `kindr_msgs/CMakeLists.txt` —— 消息生成补依赖

```diff
 rosidl_generate_interfaces(${PROJECT_NAME}
   ...
+  DEPENDENCIES std_msgs geometry_msgs
 )
```

上游 `galactic` 分支没有声明 `DEPENDENCIES`，在 Humble 上生成接口时会因缺少
`std_msgs` / `geometry_msgs` 的类型支持而失败。

## 构建

```bash
colcon build --packages-select kindr_msgs kindr_ros
```

前置：`kindr` 必须已 `make install`（见 `src/kindr/UPSTREAM.md`）。
