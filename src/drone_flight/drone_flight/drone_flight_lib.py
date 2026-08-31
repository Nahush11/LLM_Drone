import threading
import time
import os
import numpy as np
import pyvicon_datastream as pv
from pyproj import Geod
from dronekit import connect, VehicleMode, LocationGlobalRelative

# ---------------- Config ----------------
VICON_TRACKER_IP = "111.111.111.111"
OBJECT_NAME = "dynamics1"
SETTLE_S = 15

lab_lat = 53.834763521554876
lab_lon = 10.697331742076214
geoid = Geod(ellps='WGS84')

# module-level handles, set up once by init()
vicon_client = None
vehicle = None
last_position = None
last_position_time = None
_feed_started = False


def pos_to_gps_coords(x, y):
    angle = np.arctan2(y, x)
    az = np.degrees(angle)
    if az < 0:
        az += 360
    dist = np.sqrt(x**2 + y**2)
    lon, lat, _ = geoid.fwd(lab_lon, lab_lat, az, dist)
    return lon, lat


def _vicon_feed():
    global last_position, last_position_time
    while True:
        try:
            vicon_client.get_frame()
            position = vicon_client.get_segment_global_translation(OBJECT_NAME, OBJECT_NAME)
            if position is None:
                time.sleep(0.05)
                continue
            position = position * np.array([1/1000, -1/1000, 1/1000])
            rotation = vicon_client.get_segment_global_rotation_euler_xyz(OBJECT_NAME, OBJECT_NAME)
            if rotation is None:
                time.sleep(0.05)
                continue
            rotation = rotation * np.array([1, -1, -1]) * 180 / np.pi
            for i in range(3):
                if rotation[i] > 180:
                    rotation[i] -= 360
                if rotation[i] < 0:
                    rotation[i] += 360
            lon, lat = pos_to_gps_coords(position[0], position[1])
            # VELOCITY ZEROED — confirmed EKF-stability fix
            vehicle.send_mavlink(
                vehicle.message_factory.gps_input_encode(
                    0, 0, 0b00000000, 0, 0, 5,
                    int(lat * 1e7), int(lon * 1e7), position[2],
                    0.1, 0.1,
                    0, 0, 0,
                    0.1, 0.1, 0.1, 25,
                    int(rotation[2] * 1e2),
                )
            )
            time.sleep(0.05)
        except Exception as e:
            print(f"vicon feed error: {e}")
            time.sleep(0.05)


def init():
    """Connect to Vicon + Pixhawk once, start the feed, wait for EKF settle."""
    global vicon_client, vehicle, _feed_started
    if vehicle is not None:
        return  # already initialised

    vicon_client = pv.PyViconDatastream()
    if vicon_client.connect(VICON_TRACKER_IP) != pv.Result.Success:
        raise RuntimeError("Vicon connect failed")
    vicon_client.enable_segment_data()
    vicon_client.set_stream_mode(pv.StreamMode.ServerPush)
    vicon_client.set_axis_mapping(pv.Direction.Forward, pv.Direction.Left, pv.Direction.Up)
    print("Vicon connected")

    os.environ['MAVLINK20'] = '1'
    os.environ['MAVLINK_DIALECT'] = 'common'
    vehicle = connect("/dev/ttyACM0", baud=115200, wait_ready=True, timeout=80, rate=10)

    @vehicle.on_message('STATUSTEXT')
    def _st(self, name, message):
        print(f"[FC] {message.text}")

    threading.Thread(target=_vicon_feed, daemon=True).start()
    _feed_started = True
    print(f"Feed started. Waiting {SETTLE_S}s for EKF to settle...")
    time.sleep(SETTLE_S)
    print("Ready for commands.")


def _arm_and_takeoff(target_alt):
    print("Switching to GUIDED")
    vehicle.mode = VehicleMode("GUIDED")
    while vehicle.mode.name != "GUIDED":
        time.sleep(1)
    print("Pre-arm checks")
    while not vehicle.is_armable:
        print(f" waiting (ekf_ok={vehicle.ekf_ok}, gps_fix={vehicle.gps_0.fix_type})")
        time.sleep(1)
    print("Arming")
    vehicle.armed = True
    while not vehicle.armed:
        time.sleep(1)
    print(f"Taking off to {target_alt} m")
    vehicle.simple_takeoff(target_alt)
    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f" alt={alt:.2f}")
        if alt >= target_alt * 0.95:
            break
        time.sleep(0.3)


def do_hover(hover_alt=1.0, hover_seconds=15):
    """Take off, hold, land."""
    try:
        _arm_and_takeoff(hover_alt)
        print(f"HOVERING for {hover_seconds}s")
        for i in range(hover_seconds):
            alt = vehicle.location.global_relative_frame.alt
            print(f" hover {i+1}/{hover_seconds}  alt={alt:.2f}")
            time.sleep(1)
    finally:
        print("Landing")
        vehicle.mode = VehicleMode("LAND")
        time.sleep(8)


def do_spiral(radius=1.0, start_alt=0.5, end_alt=1.5, windings=3,
              duration=60.0, lookahead=1.5, rate_hz=5.0, groundspeed=0.4):
    """Fly an upward spiral."""
    def spiral_target(t):
        t = min(t, duration)
        frac = t / duration
        theta = frac * windings * 2 * np.pi
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        z = start_alt + frac * (end_alt - start_alt)
        return x, y, z

    try:
        _arm_and_takeoff(start_alt)
        print("Flying spiral")
        start_t = time.time()
        period = 1.0 / rate_hz
        while True:
            t = time.time() - start_t
            x, y, z = spiral_target(t + lookahead)
            lon, lat = pos_to_gps_coords(x, y)
            vehicle.simple_goto(LocationGlobalRelative(lat, lon, z), groundspeed=groundspeed)
            if t >= duration + lookahead:
                print("Spiral complete")
                break
            time.sleep(period)
    finally:
        print("Landing")
        vehicle.mode = VehicleMode("LAND")
        time.sleep(8)


def do_land():
    print("Landing (direct command)")
    vehicle.mode = VehicleMode("LAND")

def do_circle(radius=1.0, alt=1.0, laps=2, duration=40.0,
              lookahead=1.5, rate_hz=5.0, groundspeed=0.4):
    """Fly a flat circle at constant altitude."""
    def circle_target(t):
        t = min(t, duration)
        frac = t / duration
        theta = frac * laps * 2 * np.pi
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        return x, y, alt

    try:
        _arm_and_takeoff(alt)
        print("Flying circle")
        start_t = time.time()
        period = 1.0 / rate_hz
        while True:
            t = time.time() - start_t
            x, y, z = circle_target(t + lookahead)
            lon, lat = pos_to_gps_coords(x, y)
            vehicle.simple_goto(LocationGlobalRelative(lat, lon, z), groundspeed=groundspeed)
            if t >= duration + lookahead:
                print("Circle complete")
                break
            time.sleep(period)
    finally:
        print("Landing")
        vehicle.mode = VehicleMode("LAND")
        time.sleep(8)

def do_takeoff(alt=1.0):
    _arm_and_takeoff(alt)
