"""
ros_blender_bridge.py
─────────────────────────────────────────────────────────────────────────────
ROS → Blender Joint State Bridge
Subscribes to /joint_states and rotates mesh objects directly in Blender.

HOW TO RUN IN BLENDER
──────────────────────
In Blender's Scripting tab, open this file and click ▶ Run Script.
"""

import sys
import threading
import bpy

# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP
# ─────────────────────────────────────────────────────────────────────────────

sys.path.insert(0, "/home/ben/blender-packages")
sys.path.insert(0, "/opt/ros/noetic/lib/python3/dist-packages")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

TOPIC_NAME      = "/joint_states"
NODE_NAME       = "blender_joint_viz"
ROS1_MODE       = True
REFRESH_RATE_HZ = 60

# Maps ROS joint name → (blender_object_name, euler_axis_index)
# Axis: 0=X  1=Y  2=Z
JOINT_MAP = {
    "base_yaw":  ("Joint_Base_Motor1_Yaw", 2),  # Z axis — yaw
    "test_cube": ("TestCube",              2),  # Z axis — same rotation
}

# ─────────────────────────────────────────────────────────────────────────────
# SHARED STATE
# ─────────────────────────────────────────────────────────────────────────────

_lock         = threading.Lock()
_joint_angles = {}
_running      = True

# ─────────────────────────────────────────────────────────────────────────────
# ROS 1  (rospy)
# ─────────────────────────────────────────────────────────────────────────────

def _ros1_thread():
    import rospy
    import rospy.core
    from sensor_msgs.msg import JointState

    rospy.core._shutdown_flag = False
    rospy.core._in_shutdown = False

    def _callback(msg):
        with _lock:
            for name, pos in zip(msg.name, msg.position):
                if name in JOINT_MAP:
                    obj_name, axis = JOINT_MAP[name]
                    _joint_angles[obj_name] = (axis, float(pos))

    rospy.init_node(NODE_NAME, anonymous=True, disable_signals=True)
    rospy.Subscriber(TOPIC_NAME, JointState, _callback)
    rospy.loginfo(f"[BlenderBridge] Listening on {TOPIC_NAME}")
    rospy.spin()

# ─────────────────────────────────────────────────────────────────────────────
# ROS 2  (rclpy)
# ─────────────────────────────────────────────────────────────────────────────

def _ros2_thread():
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState

    class JointListener(Node):
        def __init__(self):
            super().__init__(NODE_NAME)
            self.create_subscription(JointState, TOPIC_NAME, self._callback, 10)
            self.get_logger().info(f"[BlenderBridge] Listening on {TOPIC_NAME}")

        def _callback(self, msg):
            with _lock:
                for name, pos in zip(msg.name, msg.position):
                    if name in JOINT_MAP:
                        obj_name, axis = JOINT_MAP[name]
                        _joint_angles[obj_name] = (axis, float(pos))

    rclpy.init()
    node = JointListener()
    try:
        while _running:
            rclpy.spin_once(node, timeout_sec=0.05)
    finally:
        node.destroy_node()
        rclpy.shutdown()

# ─────────────────────────────────────────────────────────────────────────────
# BLENDER TIMER — runs on main thread, safe to touch bpy.data
# ─────────────────────────────────────────────────────────────────────────────

def _blender_update():
    if not _running:
        return None

    with _lock:
        snapshot = dict(_joint_angles)

    for obj_name, (axis, angle) in snapshot.items():
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            continue
        obj.rotation_mode = "XYZ"
        euler = list(obj.rotation_euler)
        euler[axis] = angle
        obj.rotation_euler = euler

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

    return 1.0 / REFRESH_RATE_HZ

# ─────────────────────────────────────────────────────────────────────────────
# START / STOP
# ─────────────────────────────────────────────────────────────────────────────

_ros_thread = None

def start_bridge():
    global _running, _ros_thread

    try:
        import rospy.client
        rospy.client._init_node_args = None
    except Exception:
        pass

    _running = True

    target = _ros1_thread if ROS1_MODE else _ros2_thread
    _ros_thread = threading.Thread(target=target, daemon=True, name="_ros1_thread")
    _ros_thread.start()

    if not bpy.app.timers.is_registered(_blender_update):
        bpy.app.timers.register(_blender_update, first_interval=0.1)

    print(f"[BlenderBridge] Started — subscribed to {TOPIC_NAME}")
    print(f"[BlenderBridge] Watching joints: {list(JOINT_MAP.keys())}")


def stop_bridge():
    global _running
    _running = False
    if bpy.app.timers.is_registered(_blender_update):
        bpy.app.timers.unregister(_blender_update)
    print("[BlenderBridge] Stopped.")

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

try:
    stop_bridge()
except Exception:
    pass

import time
time.sleep(0.3)

start_bridge()
