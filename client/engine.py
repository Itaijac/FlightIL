from direct.showbase.ShowBase import ShowBase

from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Vec4,
    Vec3,
    WindowProperties,
    TextNode
)

from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DirectLabel,
    DirectEntry,
    OnscreenImage,
    OkDialog,
    YesNoDialog
)

import numpy as np
import math
import sys
import socket
from keyboard import is_pressed
from datetime import datetime

from hud import HUD
from constants import MAP, AIRCRAFT

from protocol import send_with_size, recv_by_size


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
        self.setup_all_menus()
        self.titleLogin.show()
        self.titleLoginBackdrop.show()

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

    def setup_all_menus(self):
        self.login_menu()
        self.sign_up_menu()

    def login(self, text_entered):
        if len(self.username_entry_login.get()) == 0:
            self.error_login.setText('Please fill in your username.')
        elif len(self.password_entry_login.get()) == 0:
            self.error_login.setText('Please fill in your password.')
        else:
            to_send = f"LOGR#{self.username_entry_login.get()}${self.password_entry_login.get()}".encode()
            send_with_size(self.socket, to_send)

            data = recv_by_size(self.socket)
            if data == "":
                raise Exception("Server is down")

            action, parameters = data.decode().split("#")

            if action == "LOGA":
                if int(parameters):
                    self.username = self.username_entry_login.get()
                    self.login_menu_to_select_aircraft_menu()
                else:
                    self.error_login.setText('The username or password you have entered is invalid.')

    
    def sign_up(self, text_entered):
        if len(self.username_entry_sign_up.get()) == 0:
            self.error_sign_up.setText('Please fill in your username.')
        elif len(self.password_entry_sign_up.get()) == 0:
            self.error_sign_up.setText('Please fill in your password.')
        else:
            to_send = f"SGNR#{self.username_entry_sign_up.get()}${self.password_entry_sign_up.get()}".encode()
            send_with_size(self.socket, to_send)

            data = recv_by_size(self.socket)
            if data == "":
                raise Exception("Server is down")

            action, parameters = data.decode().split("#")

            if action == "SGNA":
                if int(parameters):
                    self.username = self.username_entry_login.get()
                    self.sign_up_menu_to_select_aircraft_menu()
                else:
                    self.error_sign_up.setText('The username you have entered is already occupied by another user.')

    def login_menu(self):
        self.titleLoginBackdrop = DirectFrame(frameColor = (1, 1, 1, 1),
                                              frameSize = (-1, 1, -1, 1),
                                              image = "models/UI/background.jpg",
                                              parent = self.render2d)

        self.titleLogin = DirectFrame(frameColor = (1, 1, 1, 0))

        title = DirectLabel(text = "Welcome to Flight-IL!",
                            scale = 0.3,
                            pos = (-1.6, 0, 0.7),
                            relief = None,
                            parent = self.titleLogin,
                            text_font = self.font,
                            text_fg = (1, 1, 1, 1),
                            text_align=TextNode.ALeft)
                            
        secondary_title = DirectLabel(text = 'To log-in, fill in the details and press Enter',
                                      scale = 0.07,
                                      pos = (-1.6, 0, 0.6),
                                      relief = None,
                                      parent = self.titleLogin,
                                      text_font = self.font,
                                      text_fg = (1, 1, 1, 1),
                                      text_align=TextNode.ALeft)

        self.username_entry_login = DirectEntry(text = "", 
                                     initialText = "Enter your username",
                                     scale = 0.1,
                                     pos = (-1.6, 0, 0.3),
                                     width = 14,
                                     frameColor = (1, 1, 1, 0.4),
                                     command = self.login,
                                     focusInCommand = self.clear_username_entry_login,
                                     focusOutCommand = self.add_username_entry_login_description,
                                     parent = self.titleLogin,
                                     text_font = self.font, 
                                     text_fg = (0, 0, 0, 0.3))

        self.password_entry_login = DirectEntry(text = "",
                                     initialText = "Enter your password",
                                     scale = 0.1,
                                     pos = (-1.6, 0, 0.1),
                                     width = 14,
                                     frameColor = (1, 1, 1, 0.4),
                                     obscured = 0,
                                     command = self.login,
                                     focusInCommand = self.clear_password_entry_login,
                                     focusOutCommand = self.add_password_entry_login_description,
                                     parent = self.titleLogin,
                                     text_font = self.font,
                                     text_fg = (0, 0, 0, 0.3))

        sign_up_button = DirectButton(text = "I don't have an account",
                                      command = self.login_menu_to_sign_up_menu,
                                      pos = (-1.6, 0, -0.9),
                                      relief = None,
                                      parent = self.titleLogin,
                                      scale = 0.05,
                                      text_font = self.font,
                                      text_align=TextNode.ALeft)
        sign_up_button.setTransparency(True)

        self.error_login = DirectLabel(text = '',
                                       scale = 0.07,
                                       pos = (-1.6, 0, 0.45),
                                       relief = None,
                                       parent = self.titleLogin,
                                       text_font = self.font,
                                       text_fg = (1, 0, 0, 1),
                                       text_align=TextNode.ALeft)

        self.titleLogin.hide()
        self.titleLoginBackdrop.hide()
    
    def clear_username_entry_login(self):
        if self.username_entry_login.get() == "Enter your username":
            self.username_entry_login['text_fg'] = (0, 0, 0, 1)
            self.username_entry_login.enterText('')
    
    def add_username_entry_login_description(self):
        if len(self.username_entry_login.get()) == 0:
            self.username_entry_login['text_fg'] = (0, 0, 0, 0.3)
            self.username_entry_login.enterText("Enter your username")

    def clear_password_entry_login(self):
        if self.password_entry_login.get() == "Enter your password":
            self.password_entry_login['text_fg'] = (0, 0, 0, 1)
            self.password_entry_login['obscured'] = 1
            self.password_entry_login.enterText('')
    
    def add_password_entry_login_description(self):
        if len(self.password_entry_login.get()) == 0:
            self.password_entry_login['obscured'] = 0
            self.password_entry_login['text_fg'] = (0, 0, 0, 0.3)
            self.password_entry_login.enterText("Enter your password")

    def sign_up_menu(self):
        self.titleSignUpBackdrop = DirectFrame(frameColor = (1, 1, 1, 1),
                                              frameSize = (-1, 1, -1, 1),
                                              image = "models/UI/background.jpg",
                                              parent = self.render2d)

        self.titleSignUp = DirectFrame(frameColor = (1, 1, 1, 0))

        title = DirectLabel(text = "Welcome to Flight-IL!",
                            scale = 0.3,
                            pos = (-1.6, 0, 0.7),
                            relief = None,
                            parent = self.titleSignUp,
                            text_font = self.font,
                            text_fg = (1, 1, 1, 1),
                            text_align=TextNode.ALeft)

        secondary_title = DirectLabel(text = 'To Sign Up, fill in the details and press Enter',
                                      scale = 0.07,
                                      pos = (-1.6, 0, 0.6),
                                      relief = None,
                                      parent = self.titleSignUp,
                                      text_font = self.font,
                                      text_fg = (1, 1, 1, 1),
                                      text_align=TextNode.ALeft)

        self.username_entry_sign_up = DirectEntry(text = "", 
                                      initialText = "Enter your username",
                                      scale = 0.1,
                                      pos = (-1.6, 0, 0.3),
                                      width = 14,
                                      frameColor = (1, 1, 1, 0.4),
                                      command = self.sign_up,
                                      focusInCommand = self.clear_username_entry_sign_up,
                                      focusOutCommand = self.add_username_entry_sign_up_description,
                                      parent = self.titleSignUp,
                                      text_font = self.font,
                                      text_fg = (0, 0, 0, 0.3))

        self.password_entry_sign_up = DirectEntry(text = "",
                                      initialText = "Enter your password",
                                      scale = 0.1,
                                      pos = (-1.6, 0, 0.1),
                                      width = 14,
                                      frameColor = (1, 1, 1, 0.4),
                                      obscured = 0,
                                      command = self.sign_up,
                                      focusInCommand = self.clear_password_entry_sign_up,
                                      focusOutCommand = self.add_password_entry_sign_up_description,
                                      parent = self.titleSignUp,
                                      text_font = self.font,
                                      text_fg = (0, 0, 0, 0.3))

        sign_up_button = DirectButton(text = "I have an account",
                                      command = self.sign_up_menu_to_login_menu,
                                      pos = (-1.6, 0, -0.9),
                                      relief = None,
                                      parent = self.titleSignUp,
                                      scale = 0.05,
                                      text_font = self.font,
                                      text_align=TextNode.ALeft)
        sign_up_button.setTransparency(True)

        self.error_sign_up = DirectLabel(text = '',
                                         scale = 0.07,
                                         pos = (-1.6, 0, 0.45),
                                         relief = None,
                                         parent = self.titleSignUp,
                                         text_font = self.font,
                                         text_fg = (1, 0, 0, 1),
                                         text_align=TextNode.ALeft)

        self.titleSignUp.hide()
        self.titleSignUpBackdrop.hide()

    def clear_username_entry_sign_up(self):
        if self.username_entry_sign_up.get() == "Enter your username":
            self.username_entry_sign_up['text_fg'] = (0, 0, 0, 1)
            self.username_entry_sign_up.enterText('')
    
    def add_username_entry_sign_up_description(self):
        if len(self.username_entry_sign_up.get()) == 0:
            self.username_entry_sign_up['text_fg'] = (0, 0, 0, 0.3)
            self.username_entry_sign_up.enterText("Enter your username")

    def clear_password_entry_sign_up(self):
        if self.password_entry_sign_up.get() == "Enter your password":
            self.password_entry_sign_up['text_fg'] = (0, 0, 0, 1)
            self.password_entry_sign_up['obscured'] = 1
            self.password_entry_sign_up.enterText('')
    
    def add_password_entry_sign_up_description(self):
        if len(self.password_entry_sign_up.get()) == 0:
            self.password_entry_sign_up['text_fg'] = (0, 0, 0, 0.3)
            self.password_entry_sign_up['obscured'] = 0
            self.password_entry_sign_up.enterText("Enter your password")

    def login_menu_to_sign_up_menu(self):
        # Hide Login Menu
        self.titleLogin.hide()
        self.titleLoginBackdrop.hide()
        
        # Clear Error Messages
        self.error_login.setText('')
         
        # Reset Input Fields
        self.username_entry_sign_up['text_fg'] = (0, 0, 0, 0.3)
        self.username_entry_sign_up['focus'] = 0
        self.username_entry_sign_up.enterText("Enter your username")

        self.password_entry_sign_up['obscured'] = 0
        self.password_entry_sign_up['text_fg'] = (0, 0, 0, 0.3)
        self.password_entry_sign_up['focus'] = 0
        self.password_entry_sign_up.enterText("Enter your password")

        # Show Sign Up Menu
        self.titleSignUp.show()
        self.titleSignUpBackdrop.show()

    def sign_up_menu_to_login_menu(self):
        # Hide Sign Up Menu
        self.titleSignUp.hide()
        self.titleSignUpBackdrop.hide()

        # Clear Error Messages
        self.error_sign_up.setText('')

        # Reset Input Fields
        self.username_entry_login['text_fg'] = (0, 0, 0, 0.3)
        self.username_entry_login['focus'] = 0
        self.username_entry_login.enterText("Enter your username")

        self.password_entry_login['obscured'] = 0
        self.password_entry_login['text_fg'] = (0, 0, 0, 0.3)
        self.password_entry_login['focus'] = 0
        self.password_entry_login.enterText("Enter your password")

        # Show Login Menu
        self.titleLogin.show()
        self.titleLoginBackdrop.show()

    def select_aircraft_menu(self):
        self.titleSelectAircraftBackdrop = DirectFrame(frameColor = (1, 1, 1, 1),
                                              frameSize = (-1, 1, -1, 1),
                                              image = "models/UI/background_without_aircraft.jpg",
                                              parent = self.render2d)

        self.titleSelectAircraft = DirectFrame(frameColor = (1, 1, 1, 0))

        time = datetime.now().hour
        if time < 12:
            title_label = f"Good Morning, {self.username}"
        elif time < 16:
            title_label = f"Good Afternoon, {self.username}"
        elif time < 19:
            title_label = f"Good Evening, {self.username}"
        else:
            title_label = f"Good Night, {self.username}"

        title = DirectLabel(text = title_label,
                            scale = 0.2,
                            pos = (-1.6, 0, 0.7),
                            relief = None,
                            parent = self.titleSelectAircraft,
                            text_font = self.font,
                            text_fg = (1, 1, 1, 1),
                            text_align=TextNode.ALeft)

        secondary_title = DirectLabel(text = 'Please select an Aircraft',
                                      scale = 0.07,
                                      pos = (-1.6, 0, 0.6),
                                      relief = None,
                                      parent = self.titleSelectAircraft,
                                      text_font = self.font,
                                      text_fg = (1, 1, 1, 1),
                                      text_align=TextNode.ALeft)

        to_send = f"SHPR#".encode()
        send_with_size(self.socket, to_send)

        data = recv_by_size(self.socket)
        if data == b"":
            print('uh')
            raise Exception("Server is down")
        fields = data.decode().split("#")
        action = fields[0]
        parameters = fields[1].split('$')

        if action == "SHPA":
            self.balance = int(parameters[0])
            self.inventory = parameters[1].split('|')

        self.F_16_image = OnscreenImage(image="models/UI/select_aircraft/F-16.png",
                                       parent = self.titleSelectAircraft,
                                       scale=0.8)
        self.F_16_image.setTransparency(True)
        self.F_16_label = DirectButton(text = "General Dynamics F-16 Fighting Falcon",
                                 scale = 0.1,
                                 pos = (0, 0, -0.8),
                                 relief = None,
                                 parent = self.titleSelectAircraft,
                                 command = self.setup_world,
                                 extraArgs = ["F-16"],
                                 text_font = self.font)

        if "F-16" not in self.inventory:
            self.F_16_label.setText("PRICE: NULL")
            self.F_16_label['command'] = self.confirm_purchase
            self.F_16_label['extraArgs'] = "F-16"

        self.MiG_25PD_image = OnscreenImage(image="models/UI/select_aircraft/MiG-25PD.png",
                                       parent = self.titleSelectAircraft,
                                       scale=0.8)
        self.MiG_25PD_image.setTransparency(True)
        self.MiG_25PD_label = DirectButton(text = "Mikoyan-Gurevich MiG-25PD",
                                 scale = 0.1,
                                 pos = (0, 0, -0.8),
                                 relief = None,
                                 parent = self.titleSelectAircraft,
                                 command = self.setup_world,
                                 extraArgs = ["MiG-25PD"],
                                 text_font = self.font)

        if "MiG-25PD" not in self.inventory:
            self.MiG_25PD_label.setText("PRICE: NULL")
            self.MiG_25PD_label['command'] = self.confirm_purchase
            self.MiG_25PD_label['extraArgs'] = ["F-16"]

        self.MiG_25PD_image.hide()
        self.MiG_25PD_label.hide()

        swipe_right_button = DirectButton(frameTexture="models/UI/right_arrow.png",
                                            pos=(1.5, 0, 0),
                                            parent = self.titleSelectAircraft,
                                            # relief = DGG.FLAT,
                                            command = self.swipe_right)
        swipe_right_button.setTransparency(True)

        swipe_left_button = DirectButton(frameTexture="models/UI/left_arrow.png",
                                            pos=(-1.5, 0, 0),
                                            parent = self.titleSelectAircraft,
                                            # relief = DGG.FLAT,
                                            command = self.swipe_left)
        swipe_left_button.setTransparency(True)
    
    def confirm_purchase(self, aircraft_to_purchase):
        dialog = YesNoDialog(dialogName="YesNoCancelDialog", 
                        text=f"Are you sure you wish to buy the {aircraft_to_purchase} for NULL?",
                        command=self.purchase,
                        extraArgs = [aircraft_to_purchase])

    def purchase(self, arg, aircraft_to_purchase):
        if arg:
            to_send = f"BUYR#{aircraft_to_purchase}"
            send_with_size(self.socket, to_send)

            data = recv_by_size(self.socket)
            if data == b"":
                raise Exception("Server is down")
            action, parameters = data.decode().split("#")

            if action == "BUYA":
                print(parameters)
                if int(parameters):
                    self.OkDialog(dialogName = "Purchase Succesful",
                                text = f"Your purchase was succesful. You now own {aircraft_to_purchase}.")
                else:
                    self.OkDialog(dialogName = "Purchase Unuccesful",
                                text = f"Your purchase was unsuccesful. You do not have enough money.")

    def sign_up_menu_to_select_aircraft_menu(self):
        # Hide Sign Up Menu
        self.titleSignUp.hide()
        self.titleSignUpBackdrop.hide()

        self.select_aircraft_menu()

        # Show Login Menu
        self.titleSelectAircraft.show()
        self.titleSelectAircraftBackdrop.show()

    def login_menu_to_select_aircraft_menu(self):
        # Hide Sign Up Menu
        self.titleLogin.hide()
        self.titleLoginBackdrop.hide()

        self.select_aircraft_menu()

        # Show Login Menu
        self.titleSelectAircraft.show()
        self.titleSelectAircraftBackdrop.show()        

    def swipe_right(self):
        if not self.F_16_image.isHidden():
            self.F_16_image.hide()
            self.F_16_label.hide()

            self.MiG_25PD_image.show()
            self.MiG_25PD_label.show()

    def swipe_left(self):
        if not self.MiG_25PD_image.isHidden():
            self.MiG_25PD_image.hide()
            self.MiG_25PD_label.hide()

            self.F_16_image.show()
            self.F_16_label.show()

    def setup_world(self, aircraft):
        """
        Sets up the environment by loading terrain, aircraft and camera.
        """
        # Hide Plane Selection Menu
        self.titleSelectAircraft.hide()
        self.titleSelectAircraftBackdrop.hide()

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
