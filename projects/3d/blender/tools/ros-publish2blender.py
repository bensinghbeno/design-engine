#!/usr/bin/env python3
"""
test_publisher.py
Publishes a continuous 360° spin on /joint_states
matching the RotateMultiOperator behaviour — same objects, same Z axis.

Run with:
    source /opt/ros/noetic/setup.bash
    python3 test_publisher.py
"""
import rospy
import math
import time
from sensor_msgs.msg import JointState

DURATION_SEC = 5.0   # seconds for one full 360° rotation (matches original script)

rospy.init_node("test_pub")
pub = rospy.Publisher("/joint_states", JointState, queue_size=10)

print("[test_publisher] Publishing to /joint_states... Ctrl+C to stop.")

start = time.time()

while not rospy.is_shutdown():
    elapsed = time.time() - start
    # Loop every DURATION_SEC — same as the original rotate script
    t = (elapsed % DURATION_SEC) / DURATION_SEC  # 0.0 → 1.0
    angle = t * 2 * math.pi                       # 0 → 2π (full 360°)

    msg = JointState()
    msg.header.stamp = rospy.Time.now()
    msg.name     = ["base_yaw", "test_cube"]
    msg.position = [angle, angle]   # both spin together

    pub.publish(msg)
    time.sleep(1.0 / 60.0)   # 60 Hz — matches the timer in the original script
