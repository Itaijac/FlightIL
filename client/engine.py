import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2

from gui import GUI
from hud import HUD
from protocol import send_with_size, recv_by_size
from direct.showbase.ShowBase import ShowBase

from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3,\
    WindowProperties, Fog, LVecBase3, InputDevice

import numpy as np
import math
import sys
import socket
import pickle
import rsa
import secrets

MAP = "alps"


class FlightSimulator(ShowBase):
    """
    This class represents a flight simulator in a 3D environment.
    """

    def __init__(self, width: int, height: int, ip:str):
        """
        Constructor for the FlightSimulator class.

        Args:
            width (int): The width of the window.
            height (int): The height of the window.
        """
        ShowBase.__init__(self)
        self.disableMouse()

        self.font = loader.loadFont("models/UI/font.ttf")
        self.font.setPixelsPerUnit(250)

        properties = WindowProperties()
        properties.setSize(width, height)
        properties.setTitle("FlightIL")
        self.win.requestProperties(properties)

        # Set up the socket
        self.ip = ip
        self.socket = socket.socket()
        try:
            self.socket.connect((self.ip, 33445))
        except:
            raise ValueError("Invalid IP entered")

        # RSA key exchange - load the public key from the server
        public_key = pickle.loads(recv_by_size(self.socket))

        # Generate the key that will be used for AES
        AES_key = secrets.token_bytes(nbytes=32)

        # Encrypt the AES key using RSA's public key
        encrypted_AES_key = rsa.encrypt(AES_key, public_key)

        # Send the crypted key back to the server
        send_with_size(self.socket, encrypted_AES_key)

        # Set up the GUI
        self.GUI = GUI(self.socket, AES_key, self.font, self.render2d,
                       self.setup_world, self.cleanup, self.exit)

    def setup_world(self, aircraft: str, token: str, username: str, aircraft_specs: tuple):
        """
        Sets up the environment by loading terrain, aircraft and camera.
        """
        # Load the aircraft
        self.aircraft = loader.loadModel(f'models/aircrafts/{aircraft}.gltf')
        self.aircraft.reparentTo(render)
        self.aircraft.setPos(0, -150000, 3000)
        self.aircraft.setScale(3)

        # Load the terrain
        self.terrain = loader.loadModel(f'models/enviorment/{MAP}/{MAP}.gltf')
        self.terrain.reparentTo(render)

        min_bound, max_bound = self.terrain.getTightBounds()
        self.terrain_dimensions = max_bound - min_bound

        # Add Light
        mainLight = DirectionalLight("main light")
        mainLight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        mainLightNodePath = render.attachNewNode(mainLight)
        mainLightNodePath.setHpr(45, -45, 0)
        render.setLight(mainLightNodePath)

        ambientLight = AmbientLight("ambient light")
        ambientLight.setColor(Vec4(0.5, 0.5, 0.5, 1))
        ambientLightNodePath = render.attachNewNode(ambientLight)
        render.setLight(ambientLightNodePath)

        base.setBackgroundColor(0.52, 0.8, 0.92, 1)

        # Add Fog
        fog = Fog("Fog Name")
        fog.setColor(0.52, 0.8, 0.92)
        fog.setExpDensity(0.00005)
        self.render.setFog(fog)

        # Set up the HUD
        self.HUD = HUD()

        # Set up the values that will be used for the physic calculations
        self.velocity = Vec3(0, 500, 0)

        # This value will indicate the thrust power
        self.throttle = 1

        # Aircraft data
        self.mass, self.max_thrust = aircraft_specs
        self.built_in_angle_of_attack = 10

        # Angle of attack values
        self.AoA_x = [-90, -40, -30, 0, 30, 40, 90]

        # Corresponding lift coefficient values
        self.AoA_y = [0, -0.1, -1, 0, 1, 0.1, 0]

        # Controls
        self.sensitivity = 0.6

        # For Collisions
        self.height_map = cv2.imread(
            f"models/enviorment/{MAP}/srtm.exr", cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        self.height_map = cv2.flip(self.height_map, 0)

        # Set up the camera
        a, b = self.aircraft.getTightBounds()
        self.aircraft_size = b - a
        if aircraft == 'efroni':
            self.camera_distance = 0.7
        elif aircraft == 'tsofit':
            self.camera_distance = 0.6
        elif aircraft == 'lavie':
            self.camera_distance = 0.8
        elif aircraft == 'baz' or aircraft == 'raam':
            self.camera_distance = 1.3
        elif aircraft == 'adir':
            self.camera_distance = 1.5
        elif aircraft == 'barak' or aircraft == 'sufa':
            self.camera_distance = 1
        base.cam.setPos(LVecBase3(
            0, -4, 1)*int(self.aircraft_size[0]/3) * self.camera_distance + self.aircraft.getPos())
        base.cam.setHpr(self.aircraft.getHpr())
        base.cam.setP(base.cam.getP() + 10)

        # Set up UDP socket
        self.server_address = (self.ip, 8888)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(0.001)

        self.other_aircrafts = []

        # For the communication with the server
        self.token = token
        self.username = username

        # Get admitted to the open world
        while True:
            to_send = f"ADDS#{self.token}"
            self.udp_socket.sendto(to_send.encode(), self.server_address)
            try:
                data, server_address = self.udp_socket.recvfrom(1024)
            except:
                continue

            fields = data.decode().split('#')
            action = fields[0]
            if action == "ADDC":
                break

        # For the keyboard input
        self.key_map = {
            "pitch-down": False,
            "pitch-up": False,
            "roll-right": False,
            "roll-left": False,
            "zoom-in": False,
            "zoom-out": False,
            "change-view": False,
            "add-throttle": False,
            "sub-throttle": False,
            "reset": False,
            "quit": False
        }
        # Is there a gamepad connected?
        self.gamepad = None
        devices = base.devices.getDevices(InputDevice.DeviceClass.flight_stick)
        if devices:
            self.device = devices[0]
        else:
            # Set up the connection between the key map and the keyboard input.
            # Whenever one of the following inputs will be inputted, the function
            # "update_key_map" will change the value of self.key_map accordingly.
            self.accept("w", self.update_key_map, ["pitch-down", True])
            self.accept("w-up", self.update_key_map, ["pitch-down", False])

            self.accept("s", self.update_key_map, ["pitch-up", True])
            self.accept("s-up", self.update_key_map, ["pitch-up", False])

            self.accept("a", self.update_key_map, ["roll-left", True])
            self.accept("a-up", self.update_key_map, ["roll-left", False])

            self.accept("d", self.update_key_map, ["roll-right", True])
            self.accept("d-up", self.update_key_map, ["roll-right", False])

            self.accept("z", self.update_key_map, ["add-throttle", True])
            self.accept("z-up", self.update_key_map, ["add-throttle", False])

            self.accept("x", self.update_key_map, ["sub-throttle", True])
            self.accept("x-up", self.update_key_map, ["sub-throttle", False])

        # These inputs can not be held down so the key map is not needed
        self.accept("escape", self.toggle_game_menu)
        self.accept("r", self.reset)
        self.accept("wheel_up", self.HUD.update_zoom, extraArgs=[5])
        self.accept("wheel_down", self.HUD.update_zoom, extraArgs=[-5])

        # Set up the Tasks - an altenative to the main loop.
        taskMgr.add(self.calculate_ground_height,
                    'Calculate the height of the ground')
        taskMgr.add(self.update_aircraft_by_physics,
                    'Update aircraft by physics')
        if devices:
            taskMgr.add(self.update_aircraft_by_flight_stick_input, 'Update aircraft by input')
        else:
            taskMgr.add(self.update_aircraft_by_keyboard_input, 'Update aircraft by input')
        taskMgr.add(self.update_hud, 'Update HUD')
        taskMgr.add(self.update_aircraft_to_server,
                    'Update the server about our aircraft')
        taskMgr.add(self.update_other_aircrafts, 'Update other aircrafts')
        taskMgr.add(self.detect_collisions, 'Detect collisions')
        taskMgr.add(self.update_camera, 'Update the camera')

    # Call back function to update the keymap
    def update_key_map(self, key, state):
        self.key_map[key] = state
    
    def calculate_ground_height(self, task):
        x = int((self.aircraft.getX() + (408400/2)) * (self.height_map.shape[1]/408400))
        y = int((self.aircraft.getY() + (233000/2)) * (self.height_map.shape[0]/233000))
        try:
            self.ground_height = self.height_map[y,x][0]
        except:
            self.ground_height = 0
        return task.cont

    def calculate_ground_height(self, task):
        """
        Finds the Z value of the terrain for the (x,y) of the aircraft
        by using the height map of the terrain. 

        Returns:
            task.cont: A flag indicating that the task should continue.
        """
        x = int((self.aircraft.getX() + (self.terrain_dimensions.x/2))
                * (self.height_map.shape[1]/self.terrain_dimensions.x))
        y = int((self.aircraft.getY() + (self.terrain_dimensions.y/2))
                * (self.height_map.shape[0]/self.terrain_dimensions.y))

        # We use try-except in other to prevent the game from crashing when
        # the (x,y) is outside of the terrain.
        try:
            self.ground_height = self.height_map[y, x][0]
        except:
            self.ground_height = 0
        return task.cont

    def get_forward(self) -> Vec3:
        """
        Returns the forward vector of the aircraft.

        Returns:
            Vec3: The forward vector of the aircraft.
        """
        return render.getRelativeVector(self.aircraft, Vec3(0, 1, 0))

    def get_right(self) -> Vec3:
        """
        Returns the right vector of the aircraft.

        Returns:
            Vec3: The right vector of the aircraft.
        """
        return render.getRelativeVector(self.aircraft, Vec3(1, 0, 0))

    def get_up(self) -> Vec3:
        """
        Returns the up vector of the aircraft.

        Returns:
            Vec3: The up vector of the aircraft.
        """
        return render.getRelativeVector(self.aircraft, Vec3(0, 0, 1))

    def update_aircraft_by_physics(self, task):
        """
        Updates the aircraft's position based on physical laws.

        Args:
            task: The task manager.

        Returns:
            task.cont: A flag indicating that the task should continue.
        """

        # Calculate the local velocity of the aircraft (self.velocity is the
        # global velocity)
        local_velocity = self.aircraft.getRelativeVector(render, self.velocity)

        # Calculate the angle of attack of the aircraft, and add the built in
        # due to the wing shape
        angle_of_attack = math.degrees(
            math.atan2(-local_velocity.z, local_velocity.y))
        angle_of_attack += self.built_in_angle_of_attack

        # Calculate gravity
        gravity_direction = Vec3(0, 0, -1)
        gravity = gravity_direction * self.mass * 9.81 * 50

        # Calculate thrust
        thrust = self.get_forward() * self.max_thrust * self.throttle * 50000

        # Calculate drag
        drag_direction = -self.velocity.normalized()
        drag = drag_direction * 0.5 * self.velocity.length_squared() * 90

        # Calculate lift
        lift_coefficient = np.interp(
            angle_of_attack, self.AoA_x, self.AoA_y) * 60
        lift_direction = drag_direction.cross(self.get_right()).normalized()
        lift = lift_direction * 0.5 * self.velocity.length_squared() * lift_coefficient

        # Calculate the acceleration and update the velocity
        acceleration = (gravity + thrust + drag + lift) / self.mass
        self.velocity += acceleration * globalClock.getDt()

        # Update the aircraft's position based on the current throttle and orientation
        new_aircraft_pos = self.aircraft.getPos() + self.velocity * globalClock.getDt()
        self.aircraft.setPos(new_aircraft_pos)

        return task.cont

    def update_aircraft_by_keyboard_input(self, task):
        """
        Updates the aircraft's orientation based on user input.

        Args:
            task: The task manager.

        Returns:
            int: A flag indicating that the task should continue.
        """
        if self.key_map["roll-right"]:
            self.aircraft.setR(self.aircraft, self.sensitivity * 2)
        if self.key_map["roll-left"]:
            self.aircraft.setR(self.aircraft, -self.sensitivity * 2)
        if self.key_map["pitch-up"]:
            self.aircraft.setP(self.aircraft, self.sensitivity)
        if self.key_map["pitch-down"]:
            self.aircraft.setP(self.aircraft, -self.sensitivity)
        if self.key_map["add-throttle"]:
            if self.throttle + 0.001 < 1:
                self.throttle += 0.001
        if self.key_map["sub-throttle"]:
            if self.throttle - 0.001 >= 0.01:
                self.throttle -= 0.001
        return task.cont
    
    def update_aircraft_by_flight_stick_input(self, task):
        self.aircraft.setR(self.aircraft, self.device.axes[0].value * self.sensitivity)
        self.aircraft.setP(self.aircraft, self.device.axes[1].value * self.sensitivity)
        self.throttle = (self.device.axes[4].value + 1) / 2 # Range is from -1 to 1. set it to 0 to 1.
        self.HUD.update_zoom(self.device.axes[2].value)

        return task.cont

    def update_hud(self, task):
        """
        Updates the hud displayed on screen. In this function we pass to
        self.HUD's update function relavant information that is presented in
        the HUD, such as our position and rotation and that of other 
        aircrafts.

        Args:
            task: The task manager.

        Returns:
            int: A flag indicating that the task should continue.
        """
        aircrafts_pos = [self.aircraft.getPos()] + [aircraft.getPos()
                                                    for aircraft in self.other_aircrafts]
        aircrafts_hpr = [self.aircraft.getHpr()] + [aircraft.getHpr()
                                                    for aircraft in self.other_aircrafts]
        self.HUD.update(aircrafts_pos, aircrafts_hpr,
                        self.velocity, self.ground_height)
        return task.cont

    def update_aircraft_to_server(self, task):
        """
        Updates the server about our aircraft's position and rotation so that
        other clients will see an accurate representation of our aircraft

        Args:
            task: The task manager

        Returns:
            int: A flag indicating that the task should continue.
        """
        x, y, z = self.aircraft.getPos()
        h, p, r = self.aircraft.getHpr()
        to_send = f"UPDR#{self.token}${x}${y}${z}${h}${p}${r}"
        self.udp_socket.sendto(to_send.encode(), self.server_address)
        return task.cont

    def update_other_aircrafts(self, task):
        """
        Updates the position and rotation of other aircrafts according to the
        information given by the server.

        Args:
            task (Task): The task manager.

        Returns:
            int: A flag indicating that the task should continue.
        """
        # Receive server data. If none was sent, continue to the next task.
        try:
            data, server_address = self.udp_socket.recvfrom(1024)
        except socket.error:
            return task.cont

        # Remove all existing aircrafts to avoid duplicates.
        for aircraft in self.other_aircrafts:
            aircraft.removeNode()
        self.other_aircrafts.clear()

        # Parse server data.
        fields = data.decode().split("#")
        action = fields[0]
        if action != "UPDA":
            raise ValueError("Illegal action sent by the server")

        # Load and position other aircraft models.
        other_aircraft_data = fields[1].split("$")
        for aircraft in other_aircraft_data:
            # Skip own aircraft.
            if self.username in aircraft:
                continue

            # Parse aircraft data.
            name, aircraft_type, x, y, z, h, p, r = aircraft.split('|')

            # Type casting all values from string values to float values
            x = float(x)
            y = float(y)
            z = float(z)
            h = float(h)
            p = float(p)
            r = float(r)

            # Load aircraft model.
            aircraft_model = loader.loadModel(
                f"models/aircrafts/{aircraft_type}.gltf")
            aircraft_model.reparentTo(render)
            aircraft_model.setPos(x, y, z)
            aircraft_model.setHpr(h, p, r)
            aircraft_model.setScale(3)

            # Append aircraft model to the list of other aircrafts.
            self.other_aircrafts.append(aircraft_model)

        # Continue with the next task.
        return task.cont

    def detect_collisions(self, task):
        # Collision between aircrafts
        for other_aircraft in self.other_aircrafts:
            if self.aircraft.getPos(other_aircraft).length() < 2:
                self.blow_aircraft()
                return task.cont

        # Collision between aircraft and terrain
        if self.ground_height is not None:
            if self.aircraft.getZ() < self.ground_height:
                self.blow_aircraft()

        return task.cont

    def blow_aircraft(self):
        self.GUI.game_menu_to_select_aircraft_menu()

    def update_camera(self, task):
        # if self.key_map['roll-left'] or self.key_map['roll-right']:
        #     camera_delay = 0.1
        # elif self.key_map['pitch-up'] or self.key_map['pitch-down']:
        #     camera_delay = 0.5
        # else:
        #     camera_delay = 0.1
        camera_delay = 0.1

        camera_vector = render.getRelativeVector(
            self.aircraft, Vec3(0, -3, 0.5))
        
        camera_pos = camera_vector*int(self.aircraft_size[0] / 3) * self.camera_distance + self.aircraft.getPos()
        aircraft_pos = self.aircraft.getPos()

        base.cam.setPos(aircraft_pos + (camera_pos -
                        aircraft_pos) * (1 - camera_delay))

        camera_hpr = base.cam.getHpr()
        aircraft_hpr = self.aircraft.getHpr()
        base.cam.setHpr(aircraft_hpr + (camera_hpr -
                        aircraft_hpr) * (1 - camera_delay))

        return task.cont

    def reset(self):
        """
        Resets the aircraft to its starting position.
        """
        self.aircraft.setPos(0, 0, 3000)
        self.aircraft.setHpr(0, 0, 0)
        self.velocity = Vec3(0, 500, 0)

    def toggle_game_menu(self):
        """
        Opens/closes the game menu according to its current state.
        """
        if self.GUI.game_menu_screen.isHidden():
            self.GUI.game_menu_screen.show()
        else:
            self.GUI.game_menu_screen.hide()

    def cleanup(self):
        # Set up the connection between the key map and the keyboard input.
        # Whenever one of the following inputs will be inputted, the function
        # "update_key_map" will change the value of self.key_map accordingly.
        self.ignore("w")
        self.ignore("w-up")

        self.ignore("s")
        self.ignore("s-up")

        self.ignore("a")
        self.ignore("a-up")

        self.ignore("d")
        self.ignore("d-up")

        self.ignore("z")
        self.ignore("z-up")

        self.ignore("x")
        self.ignore("x-up")

        # These inputs can not be held down so the key map is not needed
        self.ignore("escape")
        self.ignore("r")
        self.ignore("wheel_up")
        self.ignore("wheel_down")

        taskMgr.remove('Calculate the height of the ground')
        taskMgr.remove('Update aircraft by physics')
        taskMgr.remove('Update aircraft by input')
        taskMgr.remove('Update HUD')
        taskMgr.remove('Update the server about our aircraft')
        taskMgr.remove('Update other aircrafts')
        taskMgr.remove('Detect collisions')
        taskMgr.remove('Update the camera')

        self.aircraft.removeNode()
        for aircraft in self.other_aircrafts:
            aircraft.removeNode()
        self.terrain.removeNode()

        render.clearLight()
        render.clearFog()

        self.HUD.cleanup()

    def exit(self):
        self.cleanup()
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError("No IP entered")
    game = FlightSimulator(1600, 900, sys.argv[1])
    game.run()
