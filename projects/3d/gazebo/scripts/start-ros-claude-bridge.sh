#!/bin/bash
# (1) Initialize the ROS <-> Claude bridge.
#     Starts roscore + rosbridge WebSocket server (Claude MCP on port 9090).
#     Leave this running in its own terminal, then launch Gazebo in another.

# Force system Python 3.8 ahead of conda (rosbridge needs twisted/tornado there)
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages

echo "[1/4] Stopping any existing roscore / rosbridge..."
pkill -f rosbridge 2>/dev/null
pkill -x roscore   2>/dev/null
sleep 2

echo "[2/4] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "[3/4] Starting roscore (background)..."
nohup roscore > /tmp/roscore.log 2>&1 &
sleep 4

echo "[4/4] Starting rosbridge (Claude MCP on ws://localhost:9090)..."
echo "      Leave this running; launch Gazebo in another terminal."
roslaunch rosbridge_server rosbridge_websocket.launch
