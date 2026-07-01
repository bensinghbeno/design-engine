#!/bin/bash
# Launches Gazebo with the joint1 T-shape project
# Run AFTER launch-rosbridge.sh is already running

PROJECT=/home/ben/dev/design-engine/projects/3d/gazebo/joint1

# Force system Python 3.8 ahead of conda
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages

echo "[1/2] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "[2/2] Launching Gazebo with T-shape (joint1)..."
roslaunch $PROJECT/launch/t_shape.launch
