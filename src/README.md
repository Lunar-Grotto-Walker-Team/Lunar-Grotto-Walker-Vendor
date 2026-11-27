# src/ —— 第三方包

本目录分两类：

- **入库的包**：我们改过的上游，各自带 `UPSTREAM.md`
- **导入的包**：`deps.repos` 拉下来的大体积/未改动上游，**不入库**（见 `.gitignore`）

```
src/
├── livox_ros_driver2/     ← 入库（现场 IP、baselink launch）
├── unitree_ros2/          ← 入库（setup.sh 适配）
├── BehaviorTree.ROS2/     ← 入库（deadline 修复）
├── elevation_mapping/     ← 入库（LaserSensorProcessor 径向门 + Go2 配置）
├── kindr/                 ← 入库（CMake 最低版本 3.28 → 3.16.3）
├── kindr_ros/             ← 入库（rosidl 补 DEPENDENCIES）
├── agx_arm_ros/           ← 入库（Piper 驱动 + MoveIt：park 位姿 / topic 后端 / TF 前缀）
├── Livox-SDK2/            ← 导入，不入库
├── librealsense/          ← 导入，不入库
├── realsense-ros/         ← 导入，不入库
└── agx_arm_ros/src/agx_arm_description/agx_arm_urdf/   ← 导入，不入库（嵌套路径）
```

---

## 构建顺序（重要）

**先装 SDK，再编 ROS 包。** 三个 SDK 必须 `make install` 到 `/usr/local`，
否则后面的 ROS 包链接不到。

```
① SDK 层（cmake + make install）
   1. Livox-SDK2      → /usr/local/lib/liblivox_lidar_sdk_*.so
   2. librealsense    → /usr/local/lib/librealsense2.so
   3. kindr           → /usr/local/include/kindr, /usr/local/lib/libkindr*

② ROS 层（colcon build）
   livox_ros_driver2（需先换名）· unitree_ros2 · BehaviorTree.ROS2
   · elevation_mapping · realsense-ros · kindr_ros
   · agx_arm_msgs → agx_arm_ctrl → agx_arm_description → agx_arm_moveit
     （需先导入 agx_arm_urdf，见下；agx_arm_ctrl 还需 pip install pyAgxArm）
```

---

## ① SDK 层：逐个安装

### 1. Livox-SDK2

```bash
cd src/Livox-SDK2
mkdir -p build && cd build
cmake .. && make -j$(nproc)
sudo make install && sudo ldconfig
```

装 5 个文件到 `/usr/local`：`liblivox_lidar_sdk_{shared,static}` + 3 个头文件。
**验证**：

```bash
grep LIVOX_LIDAR_SDK_MINOR_VERSION /usr/local/include/livox_lidar_def.h   # 应为 5（1.5.x）
grep kLivoxLidarTypeMid360s /usr/local/include/livox_lidar_def.h          # 应为 35
```

### 2. librealsense（Jetson 专属参数）

容器内 GCC 与 CUDA 11.4 冲突，必须指定 `gcc-10`；Jetson Orin 的计算架构是 `87`。

```bash
sudo apt install gcc-10 g++-10
export PATH=/usr/local/cuda/bin:$PATH
cd src/librealsense
mkdir -p build && cd build
cmake .. \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DFORCE_RSUSB_BACKEND=true \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-10 \
  -DCMAKE_CUDA_ARCHITECTURES=87 \
  -DBUILD_WITH_CUDA=true \
  -DBUILD_EXAMPLES=true \
  -DBUILD_GRAPHICAL_EXAMPLES=true \
  -DBUILD_PYTHON_BINDINGS=true
make -j$(nproc) && sudo make install && sudo ldconfig
```

参数含义：`FORCE_RSUSB_BACKEND` 走 USB 后端（Jetson 适配）、`CUDA_ARCHITECTURES=87`
是 Orin 架构、`CUDA_HOST_COMPILER` 指定低版本 GCC、`PYTHON_BINDINGS` 供 pyrealsense2 使用。

**验证**：`ls /usr/local/lib/librealsense2.so*`

> `librealsense` 的 `package.xml` 声明了 `<build_type>cmake</build_type>`，
> `vcs import` 之后 colcon 会把它当普通 CMake 包再编一遍（10 分钟以上，且与
> 上面 `make install` 的结果冲突）。官方包未做修改，本仓库不携带它的标记文件，
> 拉取后手动加一个：
>
> ```bash
> touch src/librealsense/COLCON_IGNORE
> ```

### 3. kindr

`elevation_mapping` 的依赖，必须用 CMake 原生方式装到系统目录：

```bash
cd src/kindr
mkdir -p build && cd build
cmake .. -DUSE_CMAKE=true
sudo make install && sudo ldconfig
```

**验证**：`ls /usr/local/include/kindr`

> `kindr` 自带 `package.xml`，colcon 会尝试编译它。**不要**让 colcon 编——
> 它需要 `-DUSE_CMAKE=true` 且必须 `make install`。
> 本仓库已在 `src/kindr/COLCON_IGNORE` 里放好标记文件，clone 下来即生效，
> 不需要手动创建。

---

## ② ROS 层：colcon 构建

### livox_ros_driver2（编译前必须换名）

```bash
cd src/livox_ros_driver2
rm -f package.xml && cp package_ROS2.xml package.xml
cp -rf launch_ROS2/ launch/
cd ../..

colcon build --symlink-install --parallel-workers 4
```

> ⚠️ **不要用官方 `./build.sh humble`**：它会删掉整个工作区的 `build/ install/`、
> 不带 `--packages-select` 编所有包、并在收尾删掉 `launch/`。
> 详见 `src/livox_ros_driver2/UPSTREAM.md`。

### 其余包

```bash
colcon build --symlink-install --parallel-workers 4
```

| 包 | 依赖 | 备注 |
|---|---|---|
| `unitree_ros2` | ROS 2 Humble | 构建 `cyclonedds_ws` 里的 `unitree_go` / `unitree_api` |
| `BehaviorTree.ROS2` | ROS 2 Humble | `behaviortree_ros2` 含本地 deadline 修复 |
| `elevation_mapping` | `kindr`（已 make install）、`grid_map`（apt） | 需要 `ros-humble-grid-map-*` |
| `realsense-ros` | `librealsense`（已 make install） | — |
| `kindr_ros` | `kindr` | — |

---

## 环境

```bash
source install/setup.bash
# CycloneDDS 配置（eth10 + AllowMulticast=spdp）由 unitree_ros2/setup.sh 提供
source src/unitree_ros2/setup.sh
```

---

## agx_arm_ros（Piper 机械臂驱动 + MoveIt）

```bash
# 1) 导入 URDF 子模块（约 205 MB，不入库）
vcs import src/agx_arm_ros/src/agx_arm_description < deps.agx-arm-urdf.repos

# 2) Python SDK（agx_arm_ctrl 的运行时依赖，不随本仓库分发）
#    上游：https://github.com/agilexrobotics/pyAgxArm（本机验证版本 1.0.0）
pip install "git+https://github.com/agilexrobotics/pyAgxArm.git"
python3 -c "import pyAgxArm; print(pyAgxArm.__version__)"   # 应输出 1.0.0

# 3) 编译（colcon 会按依赖顺序处理）
colcon build --symlink-install --packages-select \
  agx_arm_msgs agx_arm_ctrl agx_arm_description agx_arm_moveit
```

注意事项：

- `agx_arm_description/CMakeLists.txt` 会 `install(DIRECTORY agx_arm_urdf ...)`，
  **没导 URDF 子模块时这个包会构建失败**；
- `agx_arm_moveit` 依赖 MoveIt 2（`ros-humble-moveit*`）；
- `hardware_backend:=topic` 需要主仓库自写的 `agx_topic_hardware` 插件；
- 真机前置：`can_activate.sh can0 1000000`（CAN 1 Mbps）。

改动明细见 `src/agx_arm_ros/UPSTREAM.md`。

---

## 更新流程

### 跟上游更新某个入库包

```bash
git remote add up-<短名> <上游 url>          # 只需一次
git fetch up-<短名>
git subtree pull --prefix=src/<包名> up-<短名> <分支> --squash
```

冲突处理与普通 merge 一致。更新后：

1. 在对应 `UPSTREAM.md` 里记下新的上游 commit
2. **重新检查本地改动是否还在**（`git diff` 对比上游）
3. `elevation_mapping` 更新后，上游误提交的 `build/` 会回来，需要再删一次：
   `git rm -r --cached src/elevation_mapping/build && rm -rf src/elevation_mapping/build`

### 更新导入的包

```bash
vcs pull src
```

版本在仓库根 `deps.repos` 里固定，改版本就改那里的 `version` 字段。
