# LLM-Controlled Autonomous Drone

Universitätsprojekt

An indoor autonomous drone that takes **natural-language commands**, uses a
**local LLM** to understand them, and flies **predefined maneuvers** hover,
circle, and spiral  using a Vicon motion-capture system for positioning.

---

## What this project actually is

**What it is:** You type a plain-English command like *"do a spiral"* or
*"fly a circle"*. A local LLM reads your words and figures out **which**
maneuver you mean, then the drone executes that specific, pre-programmed
flight autonomously.



Think of the LLM as a smart translator between you and the drone. It's not an
autopilot that makes up flight on its own.

---

## Demo Videos

### Hover


https://github.com/user-attachments/assets/a2c38877-7abf-48cd-a8c0-480d045f5fca





### Circle




https://github.com/user-attachments/assets/8114b1ea-f104-47e2-a598-ff4390bcd5f6



### Spiral


https://github.com/user-attachments/assets/113afaa5-8083-4514-81ce-e6485d418ed1






https://github.com/user-attachments/assets/be2c5041-15b6-4bb6-a33c-23828ac5a4f7




---

## How it works

```
You type: "do a spiral"
      |
      v
[ LLM (Ollama) ]  -- understands intent, outputs a command: {"action":"spiral"}
      |
      v
[ ROS2 topic ]    -- carries the command across the network
      |
      v
[ Flight node on Raspberry Pi ]  -- runs the matching tested maneuver
      |
      v
[ Drone flies the spiral autonomously, positioned by Vicon ]
```

- The **LLM runs on a laptop** (it needs a GPU) and only does the
  text-to-command translation.
- The **flight code runs on a Raspberry Pi** connected to the flight
  controller, and executes the actual maneuver.
- The two talk over **ROS2** across the network.
- **Vicon motion capture** provides precise indoor position (injected into
  the flight controller as GPS), so the drone knows exactly where it is
  with no real GPS.

---

## System components

| Part | Role |
|------|------|
| **Ollama (LLM)** | Turns natural language into a structured command |
| **ROS2 (Jazzy)** | Passes commands between the laptop and the Pi |
| **Raspberry Pi 5** | Runs the flight code, talks to the flight controller |
| **Pixhawk 6C (ArduPilot)** | The drone's flight controller |
| **DroneKit / MAVLink** | How the Pi commands the flight controller |
| **Vicon motion capture** | Precise indoor positioning (used as GPS) |

## Available commands

The LLM maps your natural language to one of these tested maneuvers:

| Commands | Maneuver |
|----------------|----------|
| "hover", "take off and hold" | **Hover** — take off, hold position, land |
| "do a circle", "fly around" | **Circle** — flat circular path |
| "do a spiral", "spin upward" | **Spiral** — upward spiral climb |


---



*University project — Design and Control of UAVs.*
