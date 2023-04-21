from direct.showbase.ShowBase import ShowBase

from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Vec4,
    Vec3,
    WindowProperties,
)

import numpy as np
import math
import sys
import socket

from hud import HUD
from gui import GUI

from constants import MAP


class FlightSimulator(ShowBase):
    """
    This class represents a flight simulator in a 3D environment.
    """

    def __init__(self, width: int, height: int):
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
        self.win.requestProperties(properties)

        mainLight = DirectionalLight("main light")
        mainLight.setColor(Vec4(0.7, 0.7, 0.7, 1))
        self.mainLightNodePath = render.attachNewNode(mainLight)
        self.mainLightNodePath.setHpr(45, -45, 0)
        render.setLight(self.mainLightNodePath)

        ambientLight = AmbientLight("ambient light")
        ambientLight.setColor(Vec4(0.5, 0.5, 0.5, 1))
        self.ambientLightNodePath = render.attachNewNode(ambientLight)
        render.setLight(self.ambientLightNodePath)

        base.setBackgroundColor(0.52, 0.8, 0.92, 1)

        # Set up the socket
        self.socket = socket.socket()
        self.socket.connect(("127.0.0.1", 33445))

        self.GUI = GUI(self.socket, self.font, self.render2d,
                       self.setup_world, self.cleanup)

    def setup_world(self, aircraft, token, username):
        """
        Sets up the environment by loading terrain, aircraft and camera.
        """
        # Load the terrain
        self.terrain = loader.loadModel(f'models/enviorment/{MAP}/{MAP}.gltf')
        self.terrain.reparentTo(render)

        # Load the aircraft
        self.aircraft = loader.loadModel(f'models/aircrafts/{aircraft}.gltf')
        self.aircraft.reparentTo(render)
        self.aircraft.setPos(0, -150000, 3000)

        self.HUD = HUD(self.aircraft.getPos())

        self.velocity = Vec3(0, 500, 0)
        self.acceleration = Vec3()
        self.mass = 50_000

        self.throttle = 1

        # Aircraft data
        self.weight = 5000
        self.max_thrust = 100
        self.built_in_angle_of_attack = 10

        # Angle of attack values
        self.x = [-90, -40, -30, 0, 30, 40, 90]

        # Corresponding lift coefficient values
        self.y = [0, -0.1, -1, 0, 1, 0.1, 0]

        # Controls
        self.sensitivity = 0.2

        # Set up the camera
        base.cam.reparentTo(self.aircraft)
        base.cam.setPos(0, -40, 10)
        base.cam.lookAt(self.aircraft)
        base.cam.setP(base.cam.getP() + 10)

        # Set up UDP socket
        self.server_address = ('127.0.0.1', 8888)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(0.001)

        self.other_aircrafts = []

        # For the communication with the server
        self.token = token
        self.username = username

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
            "zoom-out" : False,
            "add-throttle" : False,
            "sub-throttle" : False,
            "reset" : False,
            "quit" : False
        }

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

        self.accept("escape", self.toggle_game_menu)
        self.accept("r", self.reset)
        self.accept("wheel_up", self.HUD.zoom_in)
        self.accept("wheel_down", self.HUD.zoom_out)
        
        # Tasks
        taskMgr.add(self.update_aircraft_by_physics, 'Update aircraft by physics')
        taskMgr.add(self.update_aircraft_by_input, 'Update aircraft by input')
        taskMgr.add(self.update_hud, 'Update HUD')
        taskMgr.add(self.update_other_aircrafts, 'Update other aircrafts')

    # Call back function to update the keymap
    def update_key_map(self, key, state):
        self.key_map[key] = state

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
            int: A flag indicating that the task should continue.
        """
        local_velocity = self.aircraft.getRelativeVector(render, self.velocity)
        angle_of_attack = math.degrees(
            math.atan2(-local_velocity.z, local_velocity.y)) + self.built_in_angle_of_attack

        # Calculate gravity
        gravity_direction = Vec3(0, 0, -1)
        gravity = gravity_direction * self.mass * 9.81 * 5

        # Calculate thrust
        thrust = self.get_forward() * self.max_thrust * self.throttle * 200000

        # Calculate drag
        drag_direction = -self.velocity.normalized()
        drag = drag_direction * 0.5 * self.velocity.length_squared() * 100

        # Calculate lift
        lift_coefficient = np.interp(angle_of_attack, self.x, self.y) * 30
        lift_direction = drag_direction.cross(self.get_right()).normalized()
        lift = lift_direction * 0.5 * self.velocity.length_squared() * lift_coefficient

        # Calculate the acceleration and update the velocity
        acceleration = (gravity + thrust + drag + lift) / self.mass
        self.velocity += acceleration * globalClock.getDt()

        # Update the aircraft's position based on the current throttle and orientation
        self.aircraft.setPos(self.aircraft.getPos() +
                             self.velocity * globalClock.getDt())
        return task.cont

    def update_aircraft_by_input(self, task):
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
            if self.throttle - 0.001 >= 0.05:
                self.throttle -= 0.001
        return task.cont
    
    def reset(self):
        self.aircraft.setPos(0, -150000, 3000)
        self.aircraft.setHpr(0, 0, 0)
        self.velocity = Vec3(0, 500, 0)

    def toggle_game_menu(self):
        if self.GUI.game_menu_screen.isHidden():
            self.GUI.game_menu_screen.show()
        else:
            self.GUI.game_menu_screen.hide()

    def update_hud(self, task):
        """
        Updates the hud displayed on screen.

        Args:
            task: The task manager.

        Returns:
            int: A flag indicating that the task should continue.
        """
        aircrafts_pos = [self.aircraft.getPos()] + [aircraft.getPos()
                                                    for aircraft in self.other_aircrafts]
        aircrafts_hpr = [self.aircraft.getHpr()] + [aircraft.getHpr()
                                                    for aircraft in self.other_aircrafts]
        self.HUD.update(aircrafts_pos, aircrafts_hpr, self.velocity)
        return task.cont

    def update_other_aircrafts(self, task):
        x, y, z = self.aircraft.getPos()
        h, p, r = self.aircraft.getHpr()
        to_send = f"UPDR#{self.token}${x}${y}${z}${h}${p}${r}"
        self.udp_socket.sendto(to_send.encode(), self.server_address)
        try:
            data, server_address = self.udp_socket.recvfrom(1024)
        except:
            return task.cont

        for aircraft in self.other_aircrafts:
            aircraft.removeNode()
        self.other_aircrafts.clear()

        fields = data.decode().split('#')
        action = fields[0]
        if action == "UPDA":
            other_aircrafts_data = fields[1].split('$')
            for aircraft in other_aircrafts_data:
                if self.username not in aircraft:
                    name, aircraft_type, x, y, z, h, p, r = aircraft.split('|')

                    x = float(x)
                    y = float(y)
                    z = float(z)
                    h = float(h)
                    p = float(p)
                    r = float(r)

                    new_other_aircraft = loader.loadModel(
                        f'models/aircrafts/{aircraft_type}.gltf')
                    new_other_aircraft.reparentTo(render)
                    new_other_aircraft.setPos(x, y, z)
                    new_other_aircraft.setHpr(h, p, r)
                    self.other_aircrafts.append(new_other_aircraft)

        return task.cont

    def cleanup(self):
        taskMgr.remove('Update aircraft by physics')
        taskMgr.remove('Update aircraft by input')
        taskMgr.remove('Update HUD')
        taskMgr.remove('Update other aircrafts')

        self.aircraft.removeNode()
        for aircraft in self.other_aircrafts:
            aircraft.removeNode()
        self.terrain.removeNode()
        self.HUD.cleanup()

    def exit(self):
        self.cleanup()
        sys.exit(1)

game = FlightSimulator(1600, 900)
game.run()
