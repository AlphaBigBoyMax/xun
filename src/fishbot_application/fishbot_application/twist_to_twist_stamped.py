#!/usr/bin/env python3
"""Convert geometry_msgs/Twist commands to geometry_msgs/TwistStamped."""

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node


class TwistToTwistStamped(Node):
    def __init__(self):
        super().__init__('twist_to_twist_stamped')
        self.publisher = self.create_publisher(
            TwistStamped, '/fishbot_diff_drive_controller/cmd_vel', 10)
        self.last_twist = Twist()
        self.last_command_time = self.get_clock().now()
        # Nav2 Jazzy publishes geometry_msgs/Twist on /cmd_vel_nav.
        # The diff-drive controller is configured for TwistStamped, so convert it.
        self.nav_subscription = self.create_subscription(
            Twist, '/cmd_vel_nav', self.convert, 10)
        # Manual teleoperation can also publish plain Twist on /cmd_vel_raw.
        self.raw_subscription = self.create_subscription(
            Twist, '/cmd_vel_raw', self.convert, 10)
        self.timer = self.create_timer(0.05, self.publish_command)

    def convert(self, msg: Twist) -> None:
        self.last_twist = msg
        self.last_command_time = self.get_clock().now()

    def convert_stamped(self, msg: TwistStamped) -> None:
        self.last_twist = msg.twist
        self.last_command_time = self.get_clock().now()

    def publish_command(self) -> None:
        now = self.get_clock().now()
        # Stop automatically when the input publisher disappears or times out.
        if (now - self.last_command_time).nanoseconds > 250_000_000:
            twist = Twist()
        else:
            twist = self.last_twist
        stamped = TwistStamped()
        stamped.header.stamp = now.to_msg()
        stamped.header.frame_id = 'base_link'
        stamped.twist = twist
        self.publisher.publish(stamped)


def main(args=None):
    rclpy.init(args=args)
    node = TwistToTwistStamped()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
