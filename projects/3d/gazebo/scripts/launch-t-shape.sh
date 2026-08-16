#!/bin/bash
# Launch the STABLE joint-based T-shape (t_shape.urdf) in Gazebo.
# Run start-mcp.sh FIRST (roscore + rosbridge) in another terminal.
#
# This spawns the T-shape with the prismatic+revolute joint arm that hangs
# vertically and swings when pushed. No controllers, no scripted forces.

PROJECT=/home/ben/dev/design-engine/projects/3d/gazebo/joint1

# Force system Python 3.8 ahead of conda
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages

# Make custom materials discoverable by Gazebo
export GAZEBO_RESOURCE_PATH=$PROJECT/media:${GAZEBO_RESOURCE_PATH}

echo "[1/3] Stopping ALL existing Gazebo/roslaunch instances (fresh world)..."
# Kill roslaunch parents FIRST (so they don't leave zombie gzservers),
# then any stragglers. Two passes with a wait to be thorough.
pkill -9 -f "joint1/launch/t_shape.launch"  2>/dev/null
pkill -9 -f "joint1/launch/t_world.launch"  2>/dev/null
pkill -9 -f "spawn_model"                    2>/dev/null
pkill -9 -f gzclient                         2>/dev/null
pkill -9 -f gzserver                         2>/dev/null
sleep 2
# second pass for anything that respawned / was mid-shutdown
pkill -9 -f gzclient  2>/dev/null
pkill -9 -f gzserver  2>/dev/null
sleep 2
LEFT=$(pgrep -f gzserver | xargs -r ps -o stat= -p 2>/dev/null | grep -vc Z)
echo "      live gzservers remaining: ${LEFT:-0} (defunct/zombie ones are harmless)"

echo "[2/3] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "[3/3] Launching T-shape (stable joint arm, no controllers)..."
roslaunch $PROJECT/launch/t_shape.launch
