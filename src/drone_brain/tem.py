#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class FlightNode(Node):
    def __init__(self):
        super().__init__('flight_node')
        self.subscription = self.create_subscription(
            String, '/drone_command', self.on_command, 10)
        self.get_logger().info('Flight node ready. Waiting for commands...')

    def on_command(self, msg):
        action = msg.data
        self.get_logger().info(f"Received command: {action}")

        if action == "hover":
            self.do_hover()
        elif action == "spiral":
            self.do_spiral()
        elif action == "takeoff":
            self.do_takeoff()
        elif action == "land":
            self.do_land()
        else:
            self.get_logger().warn(f"Unknown action: {action}")

    def do_hover(self):
        self.get_logger().info(">>> HOVER: (would run hover1.py logic)")

    def do_spiral(self):
        self.get_logger().info(">>> SPIRAL: (would run spiral1.py logic)")
        

    def do_takeoff(self):
        self.get_logger().info(">>> TAKEOFF")

    def do_land(self):
        self.get_logger().info(">>> LAND")


def main(args=None):
    rclpy.init(args=args)
    node = FlightNode()
    rclpy.spin(node)         
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()