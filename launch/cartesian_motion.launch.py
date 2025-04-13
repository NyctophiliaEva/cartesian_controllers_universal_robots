from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.actions import TimerAction
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    this_pkg = FindPackageShare("cartesian_controllers_universal_robots")

    # Declare arguments
    arg_simulate = DeclareLaunchArgument(
        "use_sim", default_value="true", description="Start in simulation mode.")
    arg_robot_ip = DeclareLaunchArgument(
        "robot_ip", default_value="192.168.1.101", description="The ur3 robot's IP address")
    declared_args = [arg_simulate, arg_robot_ip]

    # Get substitution variables
    use_sim = LaunchConfiguration("use_sim")

    description_file = PathJoinSubstitution([this_pkg, "urdf",
                                             "setup_simulator.urdf.xacro" if use_sim else "setup.urdf.xacro"])
    controllers_file = PathJoinSubstitution(
        [this_pkg, "config", "motion_manager.yaml"])
    rviz_config_file = PathJoinSubstitution([this_pkg, "etc", "setup.rviz"])
    robot_description_content = Command([
        FindExecutable(name="xacro"), " ",
        description_file, " ",
        "use_sim:=true", use_sim
    ])
    robot_description = {"robot_description": robot_description_content}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description]
    )
    
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        # remappings=[('/target_frame', 'cartesian_motion_controller/target_frame')],
        parameters=[robot_description, controllers_file],
    )

    # Visualization
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file]
    )

    # Gazebo仿真器
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare("gazebo_ros"), "/launch", "/gazebo.launch.py"
        ]),
        condition=IfCondition(use_sim)
    )
    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "ur3"],
        output="screen",
        condition=IfCondition(use_sim)
    )

    # Controller spawners with delays
    def spawn_controller(name, delay=0.0):
        return TimerAction(
            period=delay,
            actions=[
                Node(
                    package="controller_manager",
                    executable="spawner",
                    output="screen",
                    arguments=[name],
                )
            ]
        )

    controller_spawners = [
        spawn_controller("joint_state_broadcaster"),
        spawn_controller("cartesian_motion_controller", delay=2.0)
    ]

    nodes = [
        controller_manager,
        robot_state_publisher,
        gazebo,
        spawn_entity,
    ] + controller_spawners # + [rviz]

    return LaunchDescription(declared_args + nodes)
