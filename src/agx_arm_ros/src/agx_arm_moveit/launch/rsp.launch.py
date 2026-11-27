import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from _moveit_config_builder import build_moveit_config, declare_common_args


def _launch(context):
    follow = LaunchConfiguration("follow").perform(context)
    feedback_topic = LaunchConfiguration("feedback_topic").perform(context)
    control_topic = LaunchConfiguration("control_topic").perform(context)
    joint_states_topic = str(feedback_topic) if follow == "true" else str(control_topic)

    # TF 帧名前缀。
    # 优先用显式 frame_prefix;未给则按 namespace 派生 —— 与上游
    # agx_arm_description/launch/display.launch.py:106-112 的官方写法同构:
    #     frame_prefix = f'{ns}/' if ns else ''
    # 上游只在 display.launch.py(单机可视化)接了这一环,MoveIt 路径的
    # rsp.launch.py 没有;这里补上,让"多臂模式"在 MoveIt 路径也成立。
    #
    # 为什么要加:robot_state_publisher 的 TF publisher 发到**绝对 topic**
    # /tf、/tf_static,ROS namespace 不会改帧名 → 两条臂的 base_link→link1
    # 会互相覆盖。frame_prefix 才是隔离 TF 帧名的官方手段。
    #
    # 注意:MoveIt 的 robot_description 不带前缀,模型帧名仍是
    # world/base_link/tcp_link;做 TF lookup 的下游代码要用带前缀的名字。
    frame_prefix = LaunchConfiguration("frame_prefix").perform(context)
    namespace = LaunchConfiguration("namespace").perform(context)
    if not frame_prefix and namespace:
        frame_prefix = f"{namespace.strip('/')}/"

    moveit_config = build_moveit_config(context)

    return [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            respawn=True,
            output="screen",
            parameters=[moveit_config.robot_description,
                        {"frame_prefix": frame_prefix}],
            remappings=[("joint_states", joint_states_topic)],
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        declare_common_args()
        + [
            DeclareLaunchArgument(
                "frame_prefix",
                default_value="",
                description=(
                    "TF frame name prefix for the arm chain, e.g. 'arm1/'. "
                    "Empty = no prefix (frames are 'base_link', 'link1'...). "
                    "When empty, derived from 'namespace' (see _launch). "
                    "NOTE: only renames the frames published by "
                    "robot_state_publisher; the MoveIt robot model keeps the "
                    "canonical unprefixed names ('world', 'base_link', "
                    "'tcp_link'...)."
                ),
            ),
            OpaqueFunction(function=_launch),
        ]
    )
