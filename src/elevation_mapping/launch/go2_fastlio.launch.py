# go2_fastlio.launch.py
#
# One-shot launch for the FAST-LIO + elevation_mapping pipeline on Go2.
#
# Composition:
#   1) Include the upstream fast_lio mapping_with_livox.launch.py with rviz=false.
#      This in turn starts livox_ros_driver2 (after a 5s init TimerAction) and
#      fast_lio mapping.launch.py (which provides camera_init → map static TF).
#      (We start our own rviz below so we don't get two rviz windows.)
#   2) Wait em_delay seconds (default 10) before starting elevation_mapping. This
#      stacks on top of the 5s livox init TimerAction inside mapping_with_livox,
#      giving FAST-LIO ~5s for its own IMU/LIO convergence before
#      /cloud_registered is meaningful. The first few frames during that window
#      are empty or pre-converged; elevation_mapping would happily store them,
#      so we delay the start.
#   3) Start elevation_mapping with four Go2-tuned configs.
#   4) Start rviz2 with go2_elevmap_fastlio.rviz (elevation-map focused,
#      top-down view, GridMap display for /elevation_map, optional group of
#      post-processed layers for slope/roughness/normals).  Fast-lio raw point
#      clouds and odometry are intentionally NOT shown — the user asked for
#      elevation-only view to keep the display readable.
#
# Topic flow (after launch):
#   /livox/lidar, /livox/imu
#     -> fast_lio mapping -> /cloud_registered, /Odometry, /path
#     -> elevation_mapping -> /elevation_map, /elevation_map_raw
#
# Pre-reqs (handled outside this launch):
#   - self_l4t container running.
#   - /my_ws/l4t/nav_ws/elevmap_fastlio/install/setup.bash sourced so that
#     grid_map_rviz_plugin is discoverable by rviz2 pluginlib.
#   - grid_map / kindr / kindr_ros / grid_map_filters built in elevmap_fastlio
#     (see elevmap_ws design doc for upstream build deps).
#   - fast_lio + livox_ros_driver2 built (either in nav_ws/fastlio_livox or
#     shared under /my_ws/l4t/<other_ws>/setup.bash sourced before this launch).

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

# Suppress chatty INFO logging at the parent launch process level.
# Module-load timing: this runs BEFORE generate_launch_description() and BEFORE
# any Node forks, so every child process inherits RCUTILS_LOGGING_SEVERITY=WARN
# unless they override via --ros-args --log-level.  Use setdefault() so an
# outer launcher that wants INFO (e.g. for SLAM debugging) can still set it
# before this module is imported.
#
# This env var suppresses livox_ros_driver2 + most rclcpp loggers.  FAST-LIO's
# laserMapping logger is not silenced by env var; if needed, pass
# --ros-args --log-level WARN to the upstream launch_args.  elevation_mapping
# keeps INFO via its Node-level --log-level below.
os.environ.setdefault('RCUTILS_LOGGING_SEVERITY', 'WARN')


def generate_launch_description():
    # --- launch args ---
    # NOTE: arg name MUST NOT collide with the upstream fast_lio launch.
    # mapping_with_livox.launch.py declares `rviz` (NOT `use_rviz`).
    # Calling our arg `show_rviz` keeps it scoped to this launch file.
    show_rviz_arg = DeclareLaunchArgument(
        'show_rviz',
        default_value='True',
        description='Launch rviz2 with go2_elevmap_fastlio.rviz (elevation-map view). '
                    'Upstream fast_lio launch runs headless via rviz:=false; this '
                    'only controls OUR rviz.',
    )
    em_delay_arg = DeclareLaunchArgument(
        'em_delay',
        default_value='10.0',
        description='Seconds to wait after fast_lio starts before launching '
                    'elevation_mapping. Stacks on top of the 5s livox init '
                    'TimerAction inside mapping_with_livox.launch.py — total '
                    '~15s after launch start. FAST-LIO needs ~4-5s for IMU/LIO '
                    'init before /cloud_registered is meaningful.',
    )

    em_share = get_package_share_directory('elevation_mapping')
    em_config_dir = os.path.join(em_share, 'config')

    elevation_params = [
        os.path.join(em_config_dir, "robots", "go2_fastlio.yaml"),
        os.path.join(em_config_dir, "elevation_maps", "go2_fastlio.yaml"),
        os.path.join(em_config_dir, "sensor_processors", "livox_mid360s.yaml"),
        os.path.join(em_config_dir, "postprocessing", "go2_fastlio_postprocessor.yaml"),
    ]

    # Pull in the upstream FAST-LIO launch (livox driver + fast_lio mapping).
    # Disable its rviz - we launch our own with the elevation-focused config.
    # mapping_with_livox.launch.py:
    #   - launches livox_ros_driver2 (when launch_livox:=true, default)
    #   - waits 5s for livox IMU init
    #   - launches fast_lio mapping.launch.py with map_tf_* pass-through
    #
    # List[Tuple] 而非 dict(Humble tuple(dict) 坑,见
    # memory feedback_include_launch_dict.md)
    fast_lio_share = get_package_share_directory('fast_lio')
    fast_lio_launch_path = os.path.join(
        fast_lio_share, 'launch', 'mapping_with_livox.launch.py')

    fast_lio_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(fast_lio_launch_path),
        launch_arguments=[
            ('rviz', 'false'),
            ('launch_livox', 'true'),
        ],
    )

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

    # camera_init → map 静态 TF 由上游 mapping.launch.py 提供
    # (RPY 用 LI_init gravity 向量实测反推,默认 0.01820/0.19945/0.00813 rad,
    # 见上游 launch 注释)。elevation_mapping 直接把 map_frame_id 设成 "map",
    # 无需在这里再加一层。
    #
    # 历史:之前在这里硬编 -13° pitch 做一个 camera_init → gravity_init,
    # 由 elevation_mapping 用 map_frame_id=gravity_init 接。现在
    # 上游 launch 已经把 camera_init → map(重力对齐)直接做了,下游不再需要。
    # map 帧的 z = 重力反向,gridmap cell 存的 z 就是真高度,语义不变。
    # NOTE:若上游 mapping_with_livox.launch.py 改回不带 map TF 的版本,
    # 必须把这里重新启用,或保留 launch 内的回退声明。

    # Delay elevation_mapping start so FAST-LIO has time to converge.
    elevation_delayed = TimerAction(
        period=LaunchConfiguration('em_delay'),
        actions=[elevation_node],
    )

    # rviz focused on the elevation map (top-down ortho, GridMap on
    # /elevation_map, optional post-processed layers group for slope/roughness).
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
        em_delay_arg,
        fast_lio_include,
        elevation_delayed,
        rviz_node,
    ])