import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import launch

################### user configure parameters for ros2 start ###################
xfer_format   = 1    # 0-Pointcloud2(PointXYZRTL), 1-customized pointcloud format
multi_topic   = 0    # 0-All LiDARs share the same topic, 1-One LiDAR one topic
data_src      = 0    # 0-lidar, others-Invalid data src
publish_freq  = 10.0 # freqency of publish, 5.0, 10.0, 20.0, 50.0, etc.
output_type   = 0
frame_id      = 'livox_frame'
lvx_file_path = '/home/livox/livox_test.lvx'
cmdline_bd_code = 'livox0000000001'

cur_path = os.path.split(os.path.realpath(__file__))[0] + '/'
cur_config_path = cur_path + '../config'
user_config_path = os.path.join(cur_config_path, 'MID360s_config.json')
################### user configure parameters for ros2 end #####################

livox_ros2_params = [
    {"xfer_format": xfer_format},
    {"multi_topic": multi_topic},
    {"data_src": data_src},
    {"publish_freq": publish_freq},
    {"output_data_type": output_type},
    {"frame_id": frame_id},
    {"lvx_file_path": lvx_file_path},
    {"user_config_path": user_config_path},
    {"cmdline_input_bd_code": cmdline_bd_code}
]


def generate_launch_description():
    livox_driver = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        parameters=livox_ros2_params
        )

    # Static TF: livox_frame -> base_link.
    # Source: Livox official installation spec for Mid-360 on Unitree Go2.
    #   Translation: (0.1870, 0.0, 0.0803) m  -- 18.7 cm forward, 8 cm up
    #   Rotation:    13 deg around Y axis       -- lidar tilted down 13 deg
    #                R_y(+13) = [[ 0.9744, 0,  0.2250],
    #                            [ 0,      1,  0     ],
    #                            [-0.2250, 0,  0.9744]]
    # livox_ros_driver2 itself does NOT publish any TF (IMU frame_id is
    # hardcoded 'livox_frame' at lddc.cpp:481 but no broadcaster is included),
    # so this static publisher is the only source of livox_frame in /tf_static.
    livox_to_base_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='livox_to_base_link_tf',
        arguments=[
            "--x",     "0.1870",
            "--y",     "0.0",
            "--z",     "0.0803",
            "--roll",  "0.0",
            "--pitch", "0.2269",   # 13 deg around Y (lidar tilted down)
            "--yaw",   "0.0",
            "--frame-id",       "base_link",
            "--child-frame-id", "livox_frame",
        ],
    )

    return LaunchDescription([
        livox_driver,
        livox_to_base_tf,
        # launch.actions.RegisterEventHandler(
        #     event_handler=launch.event_handlers.OnProcessExit(
        #         target_action=livox_rviz,
        #         on_exit=[
        #             launch.actions.EmitEvent(event=launch.events.Shutdown()),
        #         ]
        #     )
        # )
    ])
