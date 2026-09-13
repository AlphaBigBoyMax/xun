import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 获取与拼接默认路径
    fishbot_navigation2_dir = get_package_share_directory(
        'fishbot_navigation2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz_config_dir = os.path.join(
        nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
    # 创建 Launch 配置
    # 默认值由下面的 DeclareLaunchArgument 提供；不要在这里传入字符串
    # default，否则某些 Jazzy 版本会将字符串拆成字符序列。
    use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time')
    autostart = launch.substitutions.LaunchConfiguration('autostart')
    map_yaml_default = os.path.join(fishbot_navigation2_dir, 'maps', 'room.yaml')
    map_yaml_path = launch.substitutions.LaunchConfiguration('map')
    nav2_param_default = os.path.join(
        fishbot_navigation2_dir, 'config', 'nav2_params.yaml')
    nav2_param_path = launch.substitutions.LaunchConfiguration('params_file')

    return launch.LaunchDescription([
        # 声明新的 Launch 参数
        launch.actions.DeclareLaunchArgument('use_sim_time', default_value='true',
                                             description='Use simulation (Gazebo) clock if true'),
        launch.actions.DeclareLaunchArgument('autostart', default_value='true',
                                             description='Automatically configure and activate Nav2'),
        launch.actions.DeclareLaunchArgument('map', default_value=map_yaml_default,
                                             description='Full path to map file to load'),
        launch.actions.DeclareLaunchArgument('params_file', default_value=nav2_param_default,
                                             description='Full path to param file to load'),

        launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_bringup_dir, '/launch', '/bringup_launch.py']),
            # 使用 Launch 参数替换原有参数
            launch_arguments={
                'map': map_yaml_path,
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'params_file': nav2_param_path}.items(),
        ),
        launch_ros.actions.Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': True}],
            output='screen'),
    ])
