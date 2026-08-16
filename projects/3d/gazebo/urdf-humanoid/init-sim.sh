#!/bin/bash
# Reset the running G1 sim back to its startup state - no Gazebo relaunch.
#
# Clears every queued force/torque, zeroes all joints, kills residual joint
# velocity, then lets the arms fall to their natural hanging rest.
#
# Usage:
#   bash init-sim.sh                # quick reset
#   bash init-sim.sh --verbose      # list every joint before and after
#   bash init-sim.sh --settle 6     # wait longer for the arms to stop moving

export PATH=/usr/bin:/usr/local/bin:$PATH
export PYTHONPATH=/opt/ros/noetic/lib/python3/dist-packages:/usr/lib/python3/dist-packages
export PYTHONNOUSERSITE=1   # stale ~/.local cffi breaks rosservice otherwise
source /opt/ros/noetic/setup.bash 2>/dev/null

HUM="$(cd "$(dirname "$0")" && pwd)"

echo "Resetting sim to startup state..."
/usr/bin/python3 "$HUM/init_sim.py" "$@"
