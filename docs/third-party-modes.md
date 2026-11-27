# 第三方依赖的引入模式

> 依据 `lg_walker_ws/docs/dev/2026-11-27-third-party-modification-guide.md` §2：
> 同一项目里可以混用五种模式，但**必须写明每个依赖用哪种模式**，否则后来者无法判断。
> 本文件就是那份名单。

模式代号沿用该指南：**A** 直接引用 / **B** 补丁文件 / **C** fork + submodule /
**D** 平铺 vendor / **E** 上游 PR。

---

## 一、名单

| 依赖 | 模式 | 位置 | 基线 | 为什么是它 |
|---|---|---|---|---|
| `livox_ros_driver2` | D（subtree 变体） | vendor `src/` | `master` @ 2144554 | 改动是现场 IP 和 launch，属团队私有适配，上游不会收（E 不成立）；改动跨 config/launch 多文件，走 B 补丁会在上游更新时整体失效 |
| `unitree_ros2` | D（subtree 变体） | vendor `src/` | tag v0.3.0（commit 66ae098） | `setup.sh` 的 Humble + eth10 + spdp 改动是本机专属；且 98% 的内容（`cyclonedds_ws`）逐字节未改，B 补丁只需 1 个文件，但上游发版节奏与 Go2 固件绑定，subtree 更省事 |
| `BehaviorTree.ROS2` | D（subtree 变体） | vendor `src/` | 0.3.0 @ 72a3bf5 | 单文件 22 行（接近 B 的 50 行阈值），但 deadline 修复将来可能想提给上游；保留完整上游历史才提得了 PR |
| `elevation_mapping` | D（subtree 变体） | vendor `src/` | `main` @ 710fffc | 改动 13 个文件约 1900 行（径向门 + Go2 全套配置），远超 B 阈值 |
| `kindr` | D（subtree 变体） | vendor `src/` | `master` @ 2446444 | 改动只有 3 行 CMake 版本，**最像 B**；但 kindr 必须以 `-DUSE_CMAKE=true` 装到 `/usr/local`，补丁模型下每次部署都要先拉上游再打补丁，多一个失败点，故选 D |
| `kindr_ros` | D（subtree 变体） | vendor `src/` | `galactic` @ af5667c | 同上，改动是 `CMakeLists.txt` 的 rosidl 依赖 |
| `Livox-SDK2` | **A** | vendor `deps.repos` | v1.5.2 | 未改动 |
| `librealsense` | **A** | vendor `deps.repos` | v2.58.3 | 未改动，78 MB |
| `realsense-ros` | **A** | vendor `deps.repos` | 4.58.3 | 未改动，94 MB |
| `point_lio_ros2` | D（独立仓库） | 主仓库 `deps.repos` | 见该仓库 `UPSTREAM.md` | 改动跨 7 组、深度耦合；**GPL-2.0**，必须与主仓库的 BSD-3 代码隔离，故单独成仓库，主仓库用 `deps.repos` 钉 commit（等价于 A 的引用方式） |
| `simple_loop_closure_ros2` | D | 主仓库 `src/` | 见该包 `UPSTREAM.md` | BSD-3，无许可隔离需求；改动跨 8 组 |

---

## 二、为什么 D 用 `git subtree`，不是直接拷贝

指南 §10 把「直接改上游副本、删掉 `.git`」列为头号陷阱（本项目 2026-11-20
事故里正是这么丢的基线）。subtree 在保持「单仓库、一次 clone 全拿到」的同时：

- 保留一个 `Squashed '<path>/' content from commit <sha>` 提交，基线可查；
- `git subtree pull --prefix=src/<pkg> up-<name> <branch> --squash` 一条命令跟上游，
  冲突只落在我们改过的那几个文件；
- `up-*` remote 只读，不推送。

它比 D 的定义（「整栈照搬、不打算跟上游」）多了跟进上游的能力，比 C
（fork + submodule）少了一个仓库和 `--recursive` 的要求。**指南的矩阵里没有这一格，
按最接近的 D 登记。**

---

## 三、为什么不用 C（fork + submodule）

指南把 C 标为「最常用」，并给出「需要跟上游、需要 review/CI」的触发条件。我们不用它，原因有三：

1. **版本组合比单包版本更重要**。这套改动的价值在于「现场 IP + `AllowMulticast=spdp`
   + BehaviorTree deadline 补丁 + kindr CMake 降版本」这一整体状态。fork 模型下 9 个仓库
   各有 HEAD，容易出现「拉了新 livox 驱动但 CycloneDDS 配置没跟上」的组合错误；
   subtree 下单仓库一个 commit 就代表整套验证过的组合。
2. **部署步骤少**。两阶段部署已经是主仓库 → vendor 两层，再加 submodule 的
   `--recursive` 和嵌套子模块，现场出错的概率上升。
3. **跨包改动**。kindr 与 kindr_ros 的适配属于同一次改动，subtree 下一个 commit 就够，
   fork 下要开两个 PR。

---

## 四、GPL 的边界

`point_lio_ros2` 是 GPL-2.0，**只能出现在它自己的仓库里**（`Lunar-Grotto-Walker-PointLIO`），
主仓库和本仓库都不得包含其代码，只能通过 `deps.repos` 引用。这样：

- 主仓库可以继续维持 BSD-3（`simple_loop_closure_ros2`）与团队自写代码的许可边界；
- GPL-2.0 的源码分发义务由那个仓库自己承担（保留 `LICENSE` + 提供源码）；
- 如果将来要闭源交付，只需替换掉这一个依赖，不必动其他仓库。

GPL-2.0 §2(a) 还要求**修改过的文件带有说明改动与日期的显著通知**，
因此 Point-LIO 仓库里我们改过的每个源文件头部都有 `[Lunar-Grotto-Walker] Modified ...` 一行。

---

## 五、维护规则

- 新增第三方依赖时，先按指南 §2 的决策树定模式，再在**本文件**加一行；没写进本文件的依赖视为违规。
- 每个入库目录必须有 `UPSTREAM.md`（上游 URL、基线 commit、改动清单）。
- 根 `NOTICE` 同步更新：新增/移除组件、许可变化都要改。
- 消费方（主仓库）钉 commit 或 tag，升级是一次显式操作。
