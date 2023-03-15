from protocol import send_with_size, recv_by_size
from datetime import datetime

from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DirectLabel,
    DirectEntry,
    OnscreenImage,
    OkDialog,
    YesNoDialog
)

from panda3d.core import TextNode

from sql import SQL

import secrets

class GUI:
    def __init__(self, socket, font, render2d, world_func):
        self.socket = socket
        self.font = font
        self.render2d = render2d
        self.world_func = world_func

        self.sql = SQL()

        self.login_menu()
        self.sign_up_menu()

        self.titleLogin.show()
        self.titleLoginBackdrop.show()

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
            raise Exception("Server is down")
        fields = data.decode().split("#")
        action = fields[0]
        parameters = fields[1].split('$')

        if action == "SHPA":
            self.balance = int(parameters[0])
            self.inventory = parameters[1].split('|')

        self.money_title = DirectLabel(text = f"Balance: {self.balance}",
                                       scale = 0.05,
                                       pos = (-1.6, 0, -0.8),
                                       relief = None,
                                       parent = self.titleSelectAircraft,
                                       text_font = self.font,
                                       text_fg = (1, 1, 1, 1),
                                       text_align=TextNode.ALeft)

        self.select_aircraft_id = 0
        self.select_aircraft_image = OnscreenImage(image="models/UI/select_aircraft/F-16.png",
                                                   parent = self.titleSelectAircraft,
                                                   scale=0.8)
        self.select_aircraft_image.setTransparency(True)
        self.select_aircraft_label = DirectButton(text = "General Dynamics F-16 Fighting Falcon",
                                                  scale = 0.1,
                                                  pos = (0, 0, -0.8),
                                                  relief = None,
                                                  parent = self.titleSelectAircraft,
                                                  command = self.select_aircraft_menu_to_world,
                                                  extraArgs = ["F-16"],
                                                  text_font = self.font)

        if self.select_aircraft_label['extraArgs'][0] not in self.inventory:
            self.select_aircraft_label.setText(f"PRICE: {self.sql.get_price(self.select_aircraft_id)}")
            self.select_aircraft_label['command'] = self.confirm_purchase
            
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
        self.confirm_purchase_dialog = YesNoDialog(dialogName="YesNoCancelDialog", 
                        text=f"Are you sure you wish to buy the {aircraft_to_purchase} for {self.sql.get_price(self.select_aircraft_id)[0]}?",
                        command=self.purchase,
                        extraArgs = [aircraft_to_purchase])

    def purchase(self, arg, aircraft_to_purchase):
        self.confirm_purchase_dialog.destroy()

        if arg:
            to_send = f"BUYR#{aircraft_to_purchase}"
            send_with_size(self.socket, to_send)

            data = recv_by_size(self.socket)
            if data == b"":
                raise Exception("Server is down")
            action, parameters = data.decode().split("#")

            if action == "BUYA":
                if int(parameters):
                    self.purchase_result_dialog = OkDialog(dialogName = "Purchase Succesful",
                                                           text = f"Your purchase was succesful. You now own {aircraft_to_purchase}.",
                                                           command = self.finish_purchase,
                                                           extraArgs = [aircraft_to_purchase])
                    self.balance -= 100
                    self.money_title.setText(f"Balance: {self.balance}")
                else:
                    self.purchase_result_dialog = OkDialog(dialogName = "Purchase Unuccesful",
                                                           text = f"Your purchase was unsuccesful. You do not have enough money.",
                                                           command = self.finish_purchase)
    
    def finish_purchase(self, arg, aircraft_purchased=None):
        self.purchase_result_dialog.destroy()
        if aircraft_purchased:
            name, description = self.sql.get_aircraft_name_and_decsription(self.select_aircraft_id)

            self.select_aircraft_image['image'] = f"models/UI/select_aircraft/{name}.png"
            self.select_aircraft_image.setTransparency(True)

            self.select_aircraft_label['text'] =  description
            self.select_aircraft_label['extraArgs'] = [name]

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
        self.select_aircraft_id = (self.select_aircraft_id + 1) % self.sql.get_aircrafts_amount()[0]
        self.update_select_aircraft_menu()

    def swipe_left(self):
        self.select_aircraft_id = (self.select_aircraft_id - 1) % self.sql.get_aircrafts_amount()[0]
        self.update_select_aircraft_menu()

    def update_select_aircraft_menu(self):
        name, description = self.sql.get_aircraft_name_and_decsription(self.select_aircraft_id)

        self.select_aircraft_image['image'] = f"models/UI/select_aircraft/{name}.png"
        self.select_aircraft_image.setTransparency(True)

        self.select_aircraft_label['text'] =  description
        self.select_aircraft_label['extraArgs'] = [name]

        if self.select_aircraft_label['extraArgs'][0] not in self.inventory:
            self.select_aircraft_label.setText(f"PRICE: {self.sql.get_price(self.select_aircraft_id)[0]}")
            self.select_aircraft_label['command'] = self.confirm_purchase

    def select_aircraft_menu_to_world(self, args):
        # Hide Plane Selection Menu
        self.titleSelectAircraft.hide()
        self.titleSelectAircraftBackdrop.hide()
        
        token = secrets.token_urlsafe(20)
        to_send = f"SELR#{self.sql.get_aircraft_name_and_decsription(self.select_aircraft_id)[0]}|{token}"
        send_with_size(self.socket, to_send)

        data = recv_by_size(self.socket)
        if data == b"":
            raise Exception("Server is down")
        action, parameters = data.decode().split("#")
        if action == "SELA":
            if int(parameters) == 1:
                self.world_func(args, token, self.username)