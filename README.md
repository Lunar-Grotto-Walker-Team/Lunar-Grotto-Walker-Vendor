# Lunar-Grotto-Walker-Vendor

月窟行者 · **第三方驱动与基础库**仓库。

主仓库 [`Lunar-Grotto-Walker`](https://github.com/Lunar-Grotto-Walker-Team/Lunar-Grotto-Walker)
只放团队自写的代码；官方库、以及在其基础上做过修改的库，统一收编到这里，
主仓库通过 `docs/dependencies.md` 引用本仓库的固定版本。

---

## 收录规则

| 情况 | 处理方式 |
|---|---|
| 官方库，**做过修改** | **入库**（`git subtree`），该子目录必须有 `UPSTREAM.md` |
| 官方库，**未修改** | **不入库**，写进根目录 `deps.repos` 固定版本，部署时 `vcs import` 拉取 |
| 团队完全自写 | 放主仓库 `src/`，不放这里 |

**为什么分两级**：`librealsense`（78 MB）+ `realsense-ros`（94 MB）占了工作树的 96%，
而它们一个字都没改。入库只会让 clone 变慢，对可复现性没有任何帮助——
`deps.repos` 里钉一个 commit 同样能保证版本一致。

**为什么单独开仓库**：第三方代码有不同的 License（Livox 是 BSD、librealsense 是 Apache-2.0、
unitree_ros2 是 BSD-3 等），混在主仓库里会让 License 边界和代码归属变得模糊；
分开后主仓库的贡献历史只反映团队自己的工作。

---

## 目录结构

本仓库同时是一个 **colcon 工作区**：

```
Lunar-Grotto-Walker-Vendor/
├── README.md
├── deps.repos            # 大体积/未改动上游的版本固定
├── .gitignore            # 忽略 deps.repos 导入的目录
└── src/
    ├── README.md         # 构建顺序 + 每个包的完整指令
    ├── livox_ros_driver2/     ← 入库（已改）
    ├── unitree_ros2/          ← 入库（已改）
    ├── BehaviorTree.ROS2/     ← 入库（已改）
    ├── elevation_mapping/     ← 入库（已改）
    ├── kindr/                 ← 入库（CMake 版本适配）
    ├── kindr_ros/             ← 入库（rosidl 依赖补齐）
    ├── Livox-SDK2/            ← 导入（不入库）
    ├── librealsense/          ← 导入（不入库）
    └── realsense-ros/         ← 导入（不入库）
```

## 部署（两阶段）

主仓库依赖本仓库，所以**先部署本仓库，再部署主仓库**。

### 第一阶段：本仓库

```bash
git clone https://github.com/Lunar-Grotto-Walker-Team/Lunar-Grotto-Walker-Vendor.git
cd Lunar-Grotto-Walker-Vendor

vcs import src < deps.repos      # 拉取大体积/未改动上游

# 官方包 librealsense 声明了 build_type=cmake，colcon 会重复编译它
touch src/librealsense/COLCON_IGNORE
# （kindr 的 COLCON_IGNORE 已随仓库提供，不用手动加）

# SDK 层（必须先 make install）
#   src/Livox-SDK2     → cmake && make install && ldconfig
#   src/librealsense   → cmake（Jetson 参数）&& make install && ldconfig
#   src/kindr          → cmake -DUSE_CMAKE=true && make install
# 完整指令见 src/README.md

colcon build --symlink-install --parallel-workers 4
source install/setup.bash
```

### 第二阶段：主仓库

```bash
git clone https://github.com/Lunar-Grotto-Walker-Team/Lunar-Grotto-Walker.git
cd Lunar-Grotto-Walker
vcs import src < deps.repos      # 指向本仓库的固定 commit
colcon build --symlink-install
```

两边的 `install/setup.bash` 都要 source，顺序：vendor → 主仓库。

## 收录清单

### 入库（改过的上游，6 个）

| 子目录 | 上游 | 版本 | 本地改动 |
|---|---|---|---|
| `src/livox_ros_driver2` | [Livox-SDK](https://github.com/Livox-SDK/livox_ros_driver2) | master @ 2144554（1.2.8） | 现场 IP、2 个 baselink launch |
| `src/unitree_ros2` | [unitreerobotics](https://github.com/unitreerobotics/unitree_ros2) | v0.3.0 @ 12c080c | `setup.sh` 适配 Humble + eth10 |
| `src/BehaviorTree.ROS2` | [BehaviorTree](https://github.com/BehaviorTree/BehaviorTree.ROS2) | 0.3.0 @ 72a3bf5 | tick 循环 deadline 修复 |
| `src/elevation_mapping` | [Muhammad540](https://github.com/Muhammad540/elevation_mapping) | main @ 710fffc | 激光径向距离门 + Go2 配置 |
| `src/kindr` | [ANYbotics](https://github.com/ANYbotics/kindr) | master @ 2446444 | CMake 最低版本 3.28 → 3.16.3 |
| `src/kindr_ros` | [SivertHavso](https://github.com/SivertHavso/kindr_ros) | galactic @ af5667c | `rosidl` 补 `DEPENDENCIES` |

### 导入（未改动的上游，见 `deps.repos`）

| 子目录 | 上游 | 版本 |
|---|---|---|
| `src/Livox-SDK2` | [Livox-SDK](https://github.com/Livox-SDK/Livox-SDK2) | v1.5.2 |
| `src/librealsense` | [IntelRealSense](https://github.com/IntelRealSense/librealsense) | v2.58.3 |
| `src/realsense-ros` | [IntelRealSense](https://github.com/IntelRealSense/realsense-ros) | 4.58.3 |

`grid_map` 不在此列 —— 本机用 apt 的 `ros-humble-grid-map-*` (2.0.1)。

---

## 导入上游：用 `git subtree`，不要直接拷贝

直接拷贝会丢掉上游历史，以后想跟上游更新只能手工 diff。`git subtree` 保留上游提交，
我们的修改是普通 commit，两者互不干扰。

```bash
# 1) 加一个只读的 upstream remote（命名约定 up-<短名>）
git remote add up-livox-ros2 https://github.com/Livox-SDK/livox_ros_driver2.git
git fetch up-livox-ros2

# 2) 导入到 src/<pkg>（--squash 把上游历史压成一个 commit，仓库不至于过大）
git subtree add --prefix=src/livox_ros_driver2 up-livox-ros2 master --squash
```

`up-*` remote **不推送**，只是本地引用，方便后续更新。

## 跟上游更新

```bash
git fetch up-livox-ros2
git subtree pull --prefix=src/livox_ros_driver2 up-livox-ros2 master --squash
```

冲突处理与普通 merge 一致。更新后请在 `UPSTREAM.md`（如果有）里记下新的上游 commit。

## 记录本地修改

对某个上游做过改动时，在该子目录新增 `UPSTREAM.md`：

```markdown
# 上游来源与本地改动

- 上游: <url>
- base commit: <sha>
- License: <name>（见同目录 LICENSE）

## 本地改动
- <文件>: <改了什么，为什么>
```

## 查看某次改动属于谁

```bash
# 只看某个子目录的历史（含我们自己的修改）
git log --oneline -- src/livox_ros_driver2

# 看上游最近一次同步点
git log --oneline --grep="Squashed 'src/livox_ros_driver2/'" 
```

---

## License

各子目录保留其上游的 `LICENSE`，**本仓库不设统一的顶层 License**——
一个仓库里混着 BSD / Apache-2.0 / GPL-2.0 的代码，挂单一 License 会误导。
分发或闭源前请逐个子目录确认。

## 与主仓库的关系

主仓库的 `docs/dependencies.md` 是唯一权威的依赖清单，本仓库的版本以那里的 commit/tag 为准。
主仓库通过 `.repos`（vcstool）拉取：

```bash
cd Lunar-Grotto-Walker
vcs import src < deps.repos
```
