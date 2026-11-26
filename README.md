# Lunar-Grotto-Walker-Vendor

月窟行者 · **第三方驱动与基础库**仓库。

主仓库 [`Lunar-Grotto-Walker`](https://github.com/Lunar-Grotto-Walker-Team/Lunar-Grotto-Walker)
只放团队自写的代码；官方库、以及在其基础上做过修改的库，统一收编到这里，
主仓库通过 `docs/dependencies.md` 引用本仓库的固定版本。

---

## 收录规则

| 情况 | 处理方式 |
|---|---|
| 官方库，**未修改** | 可以收编（便于锁定版本），也可以只在主仓库 `docs/dependencies.md` 里写来源与版本 |
| 官方库，**做过修改** | **必须**收编到这里，并在该子目录写 `UPSTREAM.md` 说明改了什么 |
| 团队完全自写 | 放主仓库 `src/`，不放这里 |

**为什么单独开仓库**：第三方代码有不同的 License（Livox 是 BSD、librealsense 是 Apache-2.0、
unitree_ros2 是 BSD-3 等），混在主仓库里会让 License 边界和代码归属变得模糊；
分开后主仓库的贡献历史只反映团队自己的工作。

---

## 目录结构

本仓库同时是一个 **colcon 工作区**：

```
Lunar-Grotto-Walker-Vendor/
├── README.md
├── .gitignore
└── src/
    └── <package_name>/        # 每个子目录 = 一个上游仓库
```

## 收录清单

> 状态：`待导入` / `已导入` / `已修改`

| 子目录 | 上游仓库 | 版本 / commit | 状态 |
|---|---|---|---|
| `src/livox_ros_driver2` | https://github.com/Livox-SDK/livox_ros_driver2 | — | 待导入 |
| `src/Livox-SDK2` | https://github.com/Livox-SDK/Livox-SDK2 | — | 待导入 |
| `src/realsense-ros` | https://github.com/IntelRealSense/realsense-ros | — | 待导入 |
| `src/librealsense` | https://github.com/IntelRealSense/librealsense | — | 待导入 |
| `src/unitree_ros2` | https://github.com/unitreerobotics/unitree_ros2 | — | 待导入 |
| `src/BehaviorTree.ROS2` | https://github.com/BehaviorTree/BehaviorTree.ROS2 | — | 待导入 |

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
