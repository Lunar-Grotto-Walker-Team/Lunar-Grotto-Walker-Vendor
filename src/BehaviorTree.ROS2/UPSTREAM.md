# 上游来源与本地改动

## 上游

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/BehaviorTree/BehaviorTree.ROS2 |
| 导入版本 | tag `0.3.0` @ `72a3bf5` |
| 导入方式 | `git subtree add --squash` |
| License | Apache-2.0（见 `LICENSE`） |

## 本地改动

### `behaviortree_ros2/src/tree_execution_server.cpp` —— 修复 tick 循环 deadline 累加

**症状**：行为树运行一段时间后"假死"——不再 tick、不响应 cancel、Ctrl-C 阻塞，
下一个 goal 卡在 `handle_accepted()` 的 `join()` 上。

**根因**：上游是 `loop_deadline += period`。`Tree::sleep()` 是可打断的
（`emitWakeUpSignal`），而 bt_ros2 的 action 节点在 feedback / result 回调里就会唤醒它。
每被提前打断一次，账上就多记约一个 `period` 的"欠账"；动作结束后没有唤醒信号了，
下一轮就把攒下的欠账一次性睡掉。

**修法**：每轮最多睡一个 `period`，并把 deadline 重新锚定到"现在"：

```cpp
const auto remaining = loop_deadline - now;
if (remaining > std::chrono::steady_clock::duration::zero()) { ... }
```

> ⚠️ 本机工作区里存在**两份** BehaviorTree.ROS2 源码（`bt_ros2_ws/` 与 `go2_bt_ws/` 的引用），
> 补丁必须两处都打，否则 `bt_runner` 链接到的仍是未修补的库（2026-11-20 踩过）。

## 相关文档

- 行为树设计规范：`l4t/go2_bt_ws/docs/bt-design-standard.md`
