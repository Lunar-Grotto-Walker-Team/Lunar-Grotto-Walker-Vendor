# src/

第三方功能包按**上游仓库名**建子目录，一个上游一个目录，不要合并。

```
src/
├── livox_ros_driver2/
├── Livox-SDK2/
├── realsense-ros/
├── librealsense/
├── unitree_ros2/
└── BehaviorTree.ROS2/
```

## 导入方式

统一用 `git subtree`（保留上游历史，可随时跟上游更新），**不要直接 `cp -r`**：

```bash
git remote add up-<短名> <上游 url>
git fetch up-<短名>
git subtree add --prefix=src/<目录名> up-<短名> <分支> --squash
```

完整流程与更新方法见仓库根目录 `README.md`。

## 目录约定

- 子目录名 = 上游仓库名（大小写保持一致），便于对照上游。
- 做过修改的子目录**必须**有 `UPSTREAM.md`，写清上游地址、base commit 和改动清单。
- 不要删上游的 `LICENSE` / `package.xml` / `CMakeLists.txt`。
- 上游自带的 `.github/`、`doc/`、`test/` 可以保留，也可以按需裁剪——
  裁剪要在 `UPSTREAM.md` 里注明，否则下次 `subtree pull` 会重新带回来。

## 编译

本仓库是 colcon 工作区，可直接构建：

```bash
colcon build --symlink-install
source install/setup.bash
```
