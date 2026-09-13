import launch
import launch_ros
import os
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 获取默认路径
    robot_name_in_model = "fishbot"
    urdf_tutorial_path = get_package_share_directory('fishbot_description')
    bridge_config_path = os.path.join(urdf_tutorial_path, 'config', 'bridge.yaml')
    default_model_path = urdf_tutorial_path + '/urdf/fishbot/fishbot.urdf.xacro'
    # 场景中的 cafe_table 网格已在 custom_room.world 中用基础几何体替代。
    default_world_path = urdf_tutorial_path + '/world/custom_room.world'
    # 为 Launch 声明参数
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_model_path),
        description='URDF 的绝对路径')
    action_declare_arg_world = launch.actions.DeclareLaunchArgument(
        name='world', default_value=default_world_path,
        description='Gazebo world 文件或 Gazebo 内置世界名称')
    # 获取文件内容生成新的参数
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),
        value_type=str)

    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            # TF 必须使用 Gazebo 的 /clock，否则会与激光消息时间错位。
            'use_sim_time': True,
        }],
        remappings=[
            ("/fishbot_diff_drive_controller/cmd_vel_unstamped","/cmd_vel"),
            ("/fishbot_diff_drive_controller/odom","/odom"),
            ("/diff_drive_controller/cmd_vel_unstamped", "/cmd_vel"),
        ],
    )

    # ROS 2 Jazzy 使用 Gazebo Harmonic（ros_gz_sim），不再使用 gazebo_ros。
    launch_gazebo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource([get_package_share_directory(
            'ros_gz_sim'), '/launch', '/gz_sim.launch.py']),
        launch_arguments={
            'gz_args': ['-r ', launch.substitutions.LaunchConfiguration('world')]
        }.items()
    )
    # 请求 Gazebo 从 robot_description 加载机器人
    spawn_entity_node = launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', '/robot_description',
                   '-entity', robot_name_in_model, ])

    # Gazebo Transport <-> ROS 2 topics。
    bridge_node = launch_ros.actions.Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config_path,
                     'use_sim_time': True}],
        output='screen',
    )

    twist_converter_node = launch_ros.actions.Node(
        package='fishbot_application',
        executable='twist_to_twist_stamped',
        output='screen',
    )

    # 加载并激活 fishbot_joint_state_broadcaster 控制器
    load_joint_state_controller = launch.actions.ExecuteProcess(
        cmd=[
            'ros2', 'run', 'controller_manager', 'spawner',
            'fishbot_joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
        ],
        output='screen'
    )

    # 加载并激活 fishbot_effort_controller 控制器
    load_fishbot_effort_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'fishbot_effort_controller'],
        output='screen'
    )

    load_fishbot_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd=[
            'ros2', 'run', 'controller_manager', 'spawner',
            'fishbot_diff_drive_controller',
            '--controller-manager', '/controller_manager',
        ],
        output='screen',
    )

    return launch.LaunchDescription([
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=spawn_entity_node,
                on_exit=[load_joint_state_controller],
            )
        ),
        # launch.actions.RegisterEventHandler(
        #     event_handler=launch.event_handlers.OnProcessExit(
        #         target_action=load_joint_state_controller,
        #         on_exit=[load_fishbot_effort_controller],
        #     )
        # ),
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=load_joint_state_controller,
                on_exit=[load_fishbot_diff_drive_controller],
            )
        ),
        action_declare_arg_mode_path,
        action_declare_arg_world,
        robot_state_publisher_node,
        launch_gazebo,
        bridge_node,
        twist_converter_node,
        spawn_entity_node,
    ])
