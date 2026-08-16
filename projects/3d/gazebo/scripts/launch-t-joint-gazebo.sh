#!/bin/bash
# (2) Launch the joint-based T-shape in Gazebo.
#     Run start-ros-claude-bridge.sh FIRST (roscore + rosbridge) in another terminal.
#     This kills any existing Gazebo instance, then spawns a fresh T-shape.

PROJECT=/home/ben/dev/design-engine/projects/3d/gazebo/joint1

# Force system Python 3.8 ahead of conda
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages

# Make custom materials (e.g. green gradient) discoverable by Gazebo
export GAZEBO_RESOURCE_PATH=$PROJECT/media:${GAZEBO_RESOURCE_PATH}

echo "[1/3] Stopping any existing Gazebo / t_shape launch..."
# Kill roslaunch parents first (so they don't leave zombie gzservers), then
# stragglers. Two passes with a wait to be thorough.
pkill -9 -f "joint1/launch/t_shape.launch" 2>/dev/null
pkill -9 -f "spawn_model"                  2>/dev/null
pkill -9 -f gzclient                       2>/dev/null
pkill -9 -f gzserver                       2>/dev/null
sleep 2
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f gzserver 2>/dev/null
sleep 2
LEFT=$(pgrep -f gzserver | xargs -r ps -o stat= -p 2>/dev/null | grep -vc Z)
echo "      live gzservers remaining: ${LEFT:-0} (defunct/zombie ones are harmless)"

echo "[2/3] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "[3/3] Launching Gazebo with T-shape (joint1)..."
roslaunch $PROJECT/launch/t_shape.launch
