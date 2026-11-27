# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/Muhammad540/elevation_mapping |
| 说明 | ANYbotics/elevation_mapping 的 ROS2 Humble 移植（基于 Aber-CRANC 的 `tf2` 分支） |
| 更上游 | https://github.com/ANYbotics/elevation_mapping |
| 导入分支 | `main` @ `710fffc`（该仓库只有一个分支，无 tag） |
| 导入方式 | `git subtree add --squash` |
| License | BSD-3-Clause（见 `LICENSE`） |

### 上游依赖（来自其 README）

| 依赖 | 来源 | 分支 / 说明 |
|---|---|---|
| `grid_map` | https://github.com/ANYbotics/grid_map | **`humble` 分支**（本机用 apt `ros-humble-grid-map-*` 2.0.1 代替） |
| `kindr` | https://github.com/ANYbotics/kindr | CMake 原生构建，`cmake .. -DUSE_CMAKE=true && sudo make install` |
| `kindr_ros` | https://github.com/SivertHavso/kindr_ros | **`galactic` 分支** |

`kindr` / `kindr_ros` 由本仓库 `deps.repos` 拉取，构建顺序见 `src/README.md`。

## 本地改动

### 1. `LaserSensorProcessor` —— 增加径向距离门（sensor frame）

| 文件 | 改动 |
|---|---|
| `include/elevation_mapping/sensor_processors/LaserSensorProcessor.hpp` | 新增 `filterPointCloudSensorType()` 声明 |
| `src/sensor_processors/LaserSensorProcessor.cpp` | 声明并读取 `sensor_processor.cutoff_min_depth` / `cutoff_max_depth`；在**传感器坐标系**按欧氏距离剔除过近/过远的点 |

上游只有地图系的 z 过滤，近距离噪声（机身反射、地面掠射）和远距离杂点会先进入
融合。这个门在点云进入 map 系之前就切掉，`cutoff_max_depth` 建议 ≤ 雷达量程。

### 2. `CMakeLists.txt` —— Boost 组件补齐

```diff
-find_package(Boost REQUIRED COMPONENTS system thread)
+find_package(Boost REQUIRED COMPONENTS system thread date_time filesystem iostreams serialization)
```

### 3. 新增 Go2 专属配置 / launch / rviz

| 文件 | 用途 |
|---|---|
| `config/robots/go2_pointlio.yaml` | Point-LIO 链的机器人参数（map frame、传感器输入、z 范围） |
| `config/robots/go2_fastlio.yaml` | FAST-LIO 链（保留，暂不使用） |
| `config/elevation_maps/go2_pointlio.yaml` | 高程图分辨率与范围 |
| `config/elevation_maps/go2_fastlio.yaml` | 同上（FAST-LIO 链） |
| `config/sensor_processors/livox_mid360s.yaml` | Mid-360S 噪声模型 + 径向门参数 |
| `config/postprocessing/go2_fastlio_postprocessor.yaml` | 旧滤波链（FAST-LIO 用） |
| `launch/go2_pointlio.launch.py` | Point-LIO 链一键启动 |
| `launch/go2_fastlio.launch.py` | FAST-LIO 链一键启动 |
| `rviz2/go2_elevmap_fastlio.rviz` | band-wide 视图（pointlio 链默认） |
| `rviz2/go2_elevmap_fastlio_cave.rviz` | cave profile，按 slope 上色 |
| `rviz2/go2_fastlio.rviz` | FAST-LIO 链视图 |

### 4. 移除上游误提交的 `build/`

上游仓库把一次 CMake 构建的 `build/` 目录（18 个文件，含 `CMakeCache.txt`、
编译好的 `a.out`）提交进了版本库。本仓库已删除，避免污染 colcon 工作区。

> ⚠️ `subtree pull` 时这些文件会回来，需要再删一次（已在 `src/README.md` 的更新流程里注明）。

### 5. 补回 `LICENSE`（2026-11-27）

上游 `Muhammad540/elevation_mapping` **没有 LICENSE 文件**，只有 `package.xml` 里的
`<license>BSD</license>` 标签。BSD-3-Clause 第 1 条要求源码再分发必须保留版权声明、
条件列表和免责声明，仅一个 SPDX 标签不构成「保留」。

本仓库从更上游 `ANYbotics/elevation_mapping` 取回 BSD-3-Clause 原文放入
`LICENSE`（`Copyright 2019, ANYbotics AG.`），未改动任何字。这属于补回上游
遗漏的许可文件，不是我们自己新增的条款。

> 如果上游后续自己补上了 LICENSE，`subtree pull` 会以他们的版本为准；
> 届时核对一下是否仍是同一份 BSD-3 文本。

## 构建

```bash
colcon build --packages-select elevation_mapping
```

前置：`kindr` 必须已 `make install`（见 `src/README.md`）。

## 相关文档

- `l4t/nav_ws/elevmap_ws/patches/` —— 2026-10 首次适配时留下的补丁集（历史参考）
- `l4t/nav_ws/elevmap_ws/user-log.md` —— 部署与调试笔记
