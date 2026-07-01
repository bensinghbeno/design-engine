#!/bin/bash
# Spawns the T-shape model into the running Gazebo world
# Run AFTER launch-gazebo-joint1.sh is up

URDF=/home/ben/dev/design-engine/projects/3d/gazebo/joint1/urdf/t_shape.urdf

export PATH=/usr/bin:/usr/local/bin:$PATH
source /opt/ros/noetic/setup.bash

echo "Removing existing t_shape (if any)..."
rosservice call /gazebo/delete_model "model_name: 't_shape'" 2>/dev/null

echo "Spawning T-shape..."
rosrun gazebo_ros spawn_model \
  -urdf \
  -model t_shape \
  -file "$URDF" \
  -x 0 -y 0 -z 0

echo "Done."
