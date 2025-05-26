# -----------------------------------------------------------------------------
# \file    robot_simulation.launch.py
# \author  Nyctophilia Rein <nyctophiliaEva@rein.ubuntu>
#
# \file    simulation.launch.py
# \author  Stefan Scherzinger <scherzin@fzi.de>
# \date    2022/02/14
#
# -----------------------------------------------------------------------------


from launch import LaunchDescription
from launch.substitutions import (
    Command, FindExecutable, PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare arguments
    this_pkg = FindPackageShare("cartesian_controllers_universal_robots")
    declared_arguments = []

    # Build the URDF with command line xacro.
    # TODO: create new URDF(e.g. sensor.urdf.xacro) to add F/T sensor
    description_file = PathJoinSubstitution([this_pkg, "urdf", "setup_sim_ur3e.urdf.xacro"])
    mujoco_model = PathJoinSubstitution([this_pkg, "etc", "scence.xml"])
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            description_file,
            " ",
            "mujoco_model:=",
            mujoco_model,
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # Robot control
    # TODO: check if match MUJOCO
    robot_controllers = PathJoinSubstitution([this_pkg, "config", "controller_manager.yaml"])

    # The actual simulation is a ROS2-control system interface.
    # Start that with the usual ROS2 controller manager mechanisms.
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        # prefix="screen -d -m gdb -command=/home/stefan/.gdb_debug_config --ex run --args",  # noqa E501
        output="both",
        remappings=[
            ('motion_control_handle/target_frame', 'target_frame'),
            ('cartesian_motion_controller/target_frame', 'target_frame'),
            ('cartesian_compliance_controller/target_frame', 'target_frame'),
            ('cartesian_force_controller/target_wrench', 'target_wrench'),
            ('cartesian_compliance_controller/target_wrench', 'target_wrench'),
            ('cartesian_force_controller/ft_sensor_wrench', 'ft_sensor_wrench'),
            ('cartesian_compliance_controller/ft_sensor_wrench', 'ft_sensor_wrench'),
            ('force_torque_sensor_broadcaster/wrench', 'ft_sensor_wrench'),
        ],
    )

    # Convenience function for easy spawner construction
    def controller_spawner(name, *args):
        return Node(
            package="controller_manager",
            executable="spawner",
            output="screen",
            arguments=[name] + [a for a in args],
        )

    # Active controllers
    active_list = [
        "joint_state_broadcaster",
        "force_torque_sensor_broadcaster",
        "scaled_joint_trajectory_controller"
    ]
    active_spawners = [controller_spawner(controller) for controller in active_list]

    # Inactive controllers
    inactive_list = [
        "cartesian_compliance_controller",
        "cartesian_force_controller",
        "cartesian_motion_controller",
        "motion_control_handle",
    ]
    inactive_spawners = [controller_spawner(controller, "--inactive") for controller in inactive_list]

    # TF tree
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    # Visualization
    # TODO: check if match MUJOCO and UR3
    rviz_config = PathJoinSubstitution([this_pkg, "etc", "robot.rviz"])
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
    )

    # Nodes to start
    nodes = (
        [control_node, robot_state_publisher, rviz]
        + active_spawners
        + inactive_spawners
    )

    return LaunchDescription(declared_arguments + nodes)
