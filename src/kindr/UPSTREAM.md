# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/ANYbotics/kindr |
| 导入分支 | `master` @ `2446444` |
| 导入方式 | `git subtree add --squash` |
| License | BSD-3-Clause（见 `LICENSE`） |

## 本地改动

### `CMakeLists.txt`（3 处）—— CMake 最低版本下调

```diff
-cmake_minimum_required(VERSION 3.28)
+cmake_minimum_required(VERSION 3.16.3)
```

改动位置：根 `CMakeLists.txt`、`test/CMakeLists.txt`、`doc/doxygen/CMakeLists.txt`。

上游 master 已要求 CMake **≥3.28**，而 Ubuntu 22.04（ROS 2 Humble 的目标平台）
自带 CMake **3.22**，直接构建会报 `CMake 3.28 or higher is required`。

下调到 3.16.3 后在本机实测可正常构建。

> 升级上游后这几行可能被改回 3.28，`git subtree pull` 后需要重新检查。

### 与本地工作区副本的其它差异（上游漂移，非本地改动）

本机 `elevmap_fastlio/src/kindr` 是较早的快照，`package.xml` 的 maintainer
还是 Remo Diethelm / Philipp Leemann 两人；上游 master 已合并成
`ANYbotics <support@anybotics.com>`。本仓库以**上游 master** 为准，未回退这处元数据。

## 构建

`elevation_mapping` 要求 kindr 以原生 CMake 方式安装到系统目录：

```bash
cd src/kindr
mkdir -p build && cd build
cmake .. -DUSE_CMAKE=true
sudo make install && sudo ldconfig
```

**不要让 colcon 编译它**（需要 `-DUSE_CMAKE=true` 且必须 `make install`）：

```bash
touch src/kindr/COLCON_IGNORE
```

验证：`ls /usr/local/include/kindr`
