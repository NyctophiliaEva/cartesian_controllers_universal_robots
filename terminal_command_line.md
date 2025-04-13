
```bash
 killall -9 ros2 gzserver gzclient rviz2
 rm -rf /dev/shm/sem.*
 rm -rf /dev/shm/rtps*
```

```bash
 2018  ros2 control list_controllers
 2019  ros2 run my_ctrl_pkg cartesian_motion_tester

 ros2 run controller_manager spawner cartesian_motion_controller
 ros2 run controller_manager spawner initial_position_controller
 ros2 run controller_manager unspawner initial_position_controller
 ros2 run controller_manager spawner initial_position_controller
 ros2 run controller_manager unspawner initial_position_controller
 ros2 run controller_manager spawner cartesian_motion_controller
```

```bash
ros2 launch cartesian_controllers_universal_robots cartesian_motion_init_pose.launch.py use_sim:=true
ros2 run my_ctrl_pkg cartesian_motion_tester
```