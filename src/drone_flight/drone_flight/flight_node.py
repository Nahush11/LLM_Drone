#!/usr/bin/env python3
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from drone_flight import drone_flight_lib as flight


class FlightNode(Node):
    def __init__(self):
        super().__init__('flight_node')
        self.busy = False
        self.subscription = self.create_subscription(
            String, '/drone_command', self.on_command, 10)
        self.get_logger().info('Connecting to drone + Vicon...')
        flight.init()
        self.get_logger().info('Flight node ready. Waiting for commands...')

    def on_command(self, msg):
        action = msg.data
        self.get_logger().info(f"Received command: {action}")

        if action in ("land", "stop"):
            flight.request_stop()
            if not self.busy:
                flight.do_land()
            return

        if self.busy:
            self.get_logger().warn("Busy flying — ignoring command.")
            return

        t = threading.Thread(target=self._run, args=(action,), daemon=True)
        t.start()

    def _run(self, action):
        self.busy = True
        try:
            if action == "hover":
                flight.do_hover()
            elif action == "spiral":
                flight.do_spiral()
            elif action == "circle":
                flight.do_circle()
            elif action == "square":
                flight.do_square()
            elif action == "takeoff":
                flight.do_takeoff()
            else:
                self.get_logger().warn(f"Unknown action: {action}")
        except Exception as e:
            self.get_logger().error(f"Flight error: {e}")
        finally:
            self.busy = False
            self.get_logger().info("Ready for next command.")


def main(args=None):
    rclpy.init(args=args)
    node = FlightNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
