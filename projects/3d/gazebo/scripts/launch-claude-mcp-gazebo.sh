#!/bin/bash
# Launch ROS + rosbridge (Claude MCP) + Gazebo for joint1 project
# Usage: bash launch-claude-mcp-gazebo.sh

PROJECT=/home/ben/dev/design-engine/projects/3d/gazebo/joint1

# Force system Python 3.8 ahead of conda so rosbridge (twisted/tornado) works
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages

echo "[1/4] Stopping any existing ROS/Gazebo processes..."
pkill -f gzserver  2>/dev/null
pkill -f gzclient  2>/dev/null
pkill -f roslaunch 2>/dev/null
pkill -f rosbridge 2>/dev/null
pkill -x roscore   2>/dev/null
sleep 3

echo "[2/4] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "[3/4] Starting roscore..."
nohup roscore > /tmp/roscore.log 2>&1 &
sleep 4

echo "[4/4] Starting rosbridge (Claude MCP on port 9090)..."
nohup roslaunch rosbridge_server rosbridge_websocket.launch > /tmp/rosbridge.log 2>&1 &
sleep 3

echo "[5/5] Launching Gazebo with joint1 project..."
roslaunch $PROJECT/launch/t_shape.launch
