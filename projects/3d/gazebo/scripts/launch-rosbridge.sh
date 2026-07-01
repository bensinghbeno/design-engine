#!/bin/bash
# Starts rosbridge WebSocket server (Claude MCP connection on port 9090)

# Force system Python 3.8 ahead of conda in PATH
export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages

echo "[1/3] Sourcing ROS Noetic..."
source /opt/ros/noetic/setup.bash

echo "[2/3] Stopping any existing rosbridge..."
pkill -f rosbridge 2>/dev/null
sleep 2

echo "[3/3] Starting rosbridge on port 9090..."
roslaunch rosbridge_server rosbridge_websocket.launch

