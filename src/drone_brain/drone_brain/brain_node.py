#!/usr/bin/env python3
# ============================================================
#  brain_node.py  —  LAPTOP side (publisher + LLM)
#  You type text -> LLM turns it into an action -> publish it
#  on /drone_command for the Pi to receive.
# ============================================================
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = """You are a drone command translator. The drone can do these actions ONLY:
- hover : take off and hold position
- spiral : fly an upward spiral
- land : land the drone
- takeoff : take off to a height

Reply with ONLY a JSON object, nothing else.
The JSON must have exactly one field "action" whose value is one of: hover, spiral, land, takeoff.

Example:
User: can you do a spiral thing
You: {"action": "spiral"}
"""


class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')
        self.publisher = self.create_publisher(String, '/drone_command', 10)
        self.get_logger().info('Brain node ready. Type a command.')

    def get_command(self, user_text):
        full_prompt = SYSTEM_PROMPT + f"\nUser: {user_text}\nYou: "
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
        })
        raw = response.json()["response"]
        data = json.loads(raw)
        return data["action"]

    def process_and_publish(self, user_text):
        try:
            action = self.get_command(user_text)
        except Exception as e:
            self.get_logger().error(f"LLM error: {e}")
            return
        msg = String()
        msg.data = action
        self.publisher.publish(msg)
        self.get_logger().info(f"'{user_text}' -> published: {action}")


def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    try:
        while True:
            user_text = input("\nCommand (or 'quit'): ")
            if user_text.lower() in ('quit', 'exit'):
                break
            node.process_and_publish(user_text)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()