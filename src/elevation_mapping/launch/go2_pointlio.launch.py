# go2_pointlio.launch.py
#
# 下游 elevation_mapping + traversability bridge,**不**起上游。
# 上游 pointlio_ws 另开一个终端启:
#
#   docker exec -w /my_ws/l4t/nav_ws/pointlio_ws self_l4t bash -c \
#     "source /my_ws/l4t/l4t_setup.sh && source install/setup.bash && \
#      ros2 launch simple_loop_closure full_stack_simple_lc_mid360s.launch.py \
#        use_livox_driver:=true show_rviz:=false"
#
# 为什么上游不 IncludeLaunchDescription:
#   1. 上游那一套是 livox driver + point_lio + simple_loop_closure + map_accumulator
#      四个节点。map_accumulator 对本节点**完全无用**(本节点吃的是单帧
#      /cloud_registered,不是 /aft_pgo_map 或 /global_pgo_map —— 全图喂进来会被
#      逐 cell 重复积分,见 robots/go2_pointlio.yaml 头注释),纯白烧 CPU。
#   2. 上游 rviz 已经占了全栈最大 CPU(54.3%),调试时能分层启停很关键。
#   3. 两个 launch 都有同名 rviz 参数,Include 时容易撞(memory: IncludeLaunchDescription
#      的 launch_arguments 会 leak 到父作用域)。
#   要一键启全栈就在外层 shell 里 `&` 串起来,不用在 launch 里耦合。
#
# Pre-reqs:
#   - self_l4t 容器在跑。
#   - 上游 pointlio_ws 已启,且:
#       ros2 run tf2_ros tf2_echo map aft_mapped   # 必须在 em_delay 内出数
#       (map → camera_init identity 静态 TF 由上游 full_stack launch:145-160 提供,
#        camera_init → aft_mapped 由 point_lio laserMapping.cpp:692 自己发)
#   - /my_ws/l4t/nav_ws/elevmap_fastlio/install/setup.bash 已 source,
#     否则 rviz2 找不到 grid_map_rviz_plugin。
#   - grid_map / kindr / kindr_ros / grid_map_filters 已在 elevmap_fastlio 编译过。
#
# DEPRECATED (2026-10-22):这个 launch 用的是 elevation_mapping,它的逐 cell
# Kalman 融合表达不了上游的回环校正 —— 回环之前写进 cell 的旧值还在,重访过的
# 地形会出现两份错开的副本(鬼影墙)。改用 pgo_gridmap_projector 的
# go2_pointlio_projected.launch.py(无状态 projector -> grid_map_filters_demo
# -> bridge)。本文件留着做参考,也留给单趟不回环、漂移无所谓的老任务。

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

# Suppress chatty INFO logging at the parent launch process level.  Module-load
# timing: this runs BEFORE generate_launch_description() and BEFORE any Node
# forks, so every child process inherits RCUTILS_LOGGING_SEVERITY=WARN.
# elevation_mapping keeps INFO via its Node-level --ros-args --log-level below.
os.environ.setdefault('RCUTILS_LOGGING_SEVERITY', 'WARN')


def generate_launch_description():
    show_rviz_arg = DeclareLaunchArgument(
        'show_rviz',
        default_value='True',
        description='Launch rviz2 with go2_elevmap_fastlio.rviz (elevation-map view).',
    )
    with_bridge_arg = DeclareLaunchArgument(
        'with_bridge',
        default_value='True',
        description='Also start terrain_traversability_bridge (GridMap -> '
                    '/terrain_traversability occupancy grid). Point-lio stack '
                    'satisfies its required_frame_id=map already, so it needs no '
                    'per-upstream override.',
    )
    em_delay_arg = DeclareLaunchArgument(
        'em_delay',
        default_value='10.0',
        description='Seconds to wait before launching elevation_mapping. Unlike '
                    'go2_fastlio.launch.py this does NOT wait for an upstream we '
                    'started ourselves — the upstream pointlio_ws runs in a '
                    'separate terminal. This delay only covers the window '
                    'between `ros2 launch` and point_lio converging; if point_lio '
                    'was started much earlier just lower it. point_lio needs '
                    '~4-5s for IMU/LIO init before /cloud_registered is '
                    'meaningful, and the first frames are pre-convergence '
                    '(elevation_mapping would happily store them).',
    )
    em_share = get_package_share_directory('elevation_mapping')
    em_config_dir = os.path.join(em_share, 'config')

    # NOTE: first two files are the point_lio-specific ones; the last two are
    # shared with go2_fastlio.launch.py unchanged:
    #   sensor_processors/livox_mid360s.yaml — 同一颗 Mid-360S,
    #     且它的值全在 root `sensor_processor.*` 命名空间(代码不读的 dead config),
    #     真正生效的噪声模型在 robots/go2_pointlio.yaml。留着只为 spec 参考对照。
    #   postprocessing/go2_fastlio_postprocessor.yaml — 纯几何滤波
    #     (inpaint / mean_in_radius / normals / slope / roughness),不依赖上游 LIO,
    #     而且半径是按 0.10m/cell 标定的,两边 resolution 相同所以直接复用。
    elevation_params = [
        os.path.join(em_config_dir, "robots", "go2_pointlio.yaml"),
        os.path.join(em_config_dir, "elevation_maps", "go2_pointlio.yaml"),
        os.path.join(em_config_dir, "sensor_processors", "livox_mid360s.yaml"),
        os.path.join(em_config_dir, "postprocessing", "go2_fastlio_postprocessor.yaml"),
    ]

    elevation_node = Node(
        package='elevation_mapping',
        executable='elevation_mapping',
        name='elevation_mapping',
        output='screen',
        # Counter the WARN-only env var set above; elevation_mapping keeps INFO
        # so its lifecycle / parameter / topic warnings stay visible.
        arguments=['--ros-args', '--log-level', 'INFO'],
        parameters=elevation_params,
    )

    # Delay elevation_mapping so point_lio has time to converge.
    elevation_delayed = TimerAction(
        period=LaunchConfiguration('em_delay'),
        actions=[elevation_node],
    )

    # bridge.launch.py only takes a params_file arg which already defaults to the
    # package's own config/bridge_params.yaml (required_frame_id=map,
    # target_resolution=0.05, slope/roughness thresholds).  Nothing to override,
    # so no launch_arguments here.
    #
    # bridge_node.py is purely reactive — no timer, and before the first
    # /elevation_map arrives it just sits in spin() silently (no warning to
    # suppress).  So it needs no TimerAction behind elevation_mapping; start it
    # immediately.
    bridge_launch_path = os.path.join(
        get_package_share_directory('elevation_traversability_bridge'),
        'launch', 'bridge.launch.py',
    )
    bridge_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(bridge_launch_path),
        condition=IfCondition(LaunchConfiguration('with_bridge')),
    )

    # rviz focused on the elevation map (top-down ortho, GridMap on
    # /elevation_map, optional post-processed layers group for slope/roughness).
    # Reuses the fastlio config — same GridMap topic names, same layer names,
    # nothing in it references a frame or upstream topic that differs.
    rviz_config = os.path.join(em_share, 'rviz2', 'go2_elevmap_fastlio.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
        condition=IfCondition(LaunchConfiguration('show_rviz')),
    )

    return LaunchDescription([
        show_rviz_arg,
        with_bridge_arg,
        em_delay_arg,
        elevation_delayed,
        bridge_include,
        rviz_node,
    ])