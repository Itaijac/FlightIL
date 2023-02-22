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
from keyboard import is_pressed

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

        self.GUI = GUI(self.socket, self.font, self.render2d, self.setup_world)


    def setup_world(self, aircraft):
        """
        Sets up the environment by loading terrain, aircraft and camera.
        """
        # Load the terrain
        self.terrain = loader.loadModel(f'models/enviorment/{MAP}/{MAP}.gltf')
        self.terrain.reparentTo(render)

        # Load the aircraft
        self.aircraft = loader.loadModel(f'models/aircrafts/{aircraft}.gltf')
        self.aircraft.reparentTo(render)
        self.aircraft.setPos(0, -25000, 3000)

        self.HUD = HUD(self.aircraft.getPos())

        self.velocity = Vec3(0, 500, 0)
        self.acceleration = Vec3()
        self.mass = 10_000

        self.throttle = 1

        # Aircraft data
        self.weight = 5000
        self.max_thrust = 100
        self.built_in_angle_of_attack = 5

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

        # Tasks
        taskMgr.add(self.update_aircraft_by_physics,'Update aircraft by physics')
        taskMgr.add(self.update_aircraft_by_input, 'Update aircraft by input')
        taskMgr.add(self.update_hud, 'Update HUD')

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
        angle_of_attack = math.degrees(math.atan2(-local_velocity.z, local_velocity.y))

        # Calculate gravity
        gravity_direction = Vec3(0, 0, -1)
        gravity = gravity_direction * self.mass * 9.81

        # Calculate thrust
        thrust = self.get_forward() * self.max_thrust * self.throttle * 2000

        # Calculate drag
        drag_direction = -self.velocity.normalized()
        drag = drag_direction * 0.5 * self.velocity.length_squared()

        # Calculate lift
        lift_coefficient = np.interp(angle_of_attack, self.x, self.y) * 4
        lift_direction = drag_direction.cross(self.get_right()).normalized()
        lift = lift_direction * 0.5 * self.velocity.length_squared() * lift_coefficient

        # Calculate the acceleration and update the velocity
        acceleration = (gravity + thrust + drag + lift) / self.mass
        self.velocity += acceleration * globalClock.getDt()

        # Update the aircraft's position based on the current throttle and orientation
        self.aircraft.setPos(self.aircraft.getPos() + self.velocity * globalClock.getDt())
        return task.cont

    def update_aircraft_by_input(self, task):
        """
        Updates the aircraft's orientation based on user input.

        Args:
            task: The task manager.

        Returns:
            int: A flag indicating that the task should continue.
        """
        if is_pressed('d'):
            self.aircraft.setR(self.aircraft, self.sensitivity * 2)
        elif is_pressed('a'):
            self.aircraft.setR(self.aircraft, -self.sensitivity * 2)
        if is_pressed('s'):
            self.aircraft.setP(self.aircraft, self.sensitivity)
        elif is_pressed('w'):
            self.aircraft.setP(self.aircraft, -self.sensitivity)
        if is_pressed('z'):
            if self.throttle + 0.001 < 1:
                self.throttle += 0.001
        elif is_pressed('x'):
            if self.throttle - 0.001 >= 0.05:
                self.throttle -= 0.001
        return task.cont

    def update_hud(self, task):
        """
        Updates the hud displayed on screen.

        Args:
            task: The task manager.

        Returns:
            int: A flag indicating that the task should continue.
        """
        self.HUD.update(self.aircraft.getPos(), self.aircraft.getHpr(), self.velocity)
        return task.cont

    def cleanup(self):
        self.aircraft.removeNode()
        self.terrain.removeNode()
        del self.HUD

    def exit(self):
        self.cleanup()
        sys.exit(1)

    def reset(self):
        self.cleanup()
        self.setup()


game = FlightSimulator(1920, 1080)
game.run()
