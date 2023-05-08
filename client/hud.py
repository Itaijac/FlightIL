from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import TextNode
from panda3d.core import Texture

import numpy as np
import cv2
import imutils

MAP = "alps"

class HUD:
    def __init__(self):
        # Initialize altitude HUD element
        self.heightHUD = OnscreenText(text="0", pos=(0.675, 0 + 0.025), scale=0.05,
                                      fg=(70, 192, 22, 255), mayChange=True, align=TextNode.ARight)

        # Initialize velocity HUD element
        self.velocityHUD = OnscreenText(text="0", pos=(-0.675, 0 + 0.025), scale=0.05,
                                        fg=(70, 192, 22, 255), mayChange=True, align=TextNode.ALeft)

        # Initialize heading HUD element
        self.headingHUD = OnscreenImage(image="models/HUD/heading.png", pos=(0, 0, 0), scale=(0.8, 0.1, 0.1))
        self.headingHUD.setTransparency(True)

        # Read and flip the environment map image
        self.map_img = cv2.imread(f"models/enviorment/{MAP}/GOOGLE_SAT_WM.tif", cv2.IMREAD_UNCHANGED)
        self.map_img = cv2.flip(self.map_img, 0)

        # Read and flip the aircraft icon image
        self.aircraft_icon_img = cv2.imread(f"models/HUD/f16-icon.png", cv2.IMREAD_UNCHANGED)
        self.aircraft_icon_img = cv2.flip(self.aircraft_icon_img, 0)

        # Initialize minimap texture
        self.minimap_texture = Texture()

        # Initialize minimap HUD element
        self.minimapHUD = OnscreenImage(image=self.minimap_texture, pos=(1.4, 0, -0.55), scale=0.4)

        # Read and flip the compass image
        self.compass_img = cv2.imread(f"models/HUD/compass.png", cv2.IMREAD_UNCHANGED)
        self.compass_img = cv2.flip(self.compass_img, 0)

        # Initialize compass texture
        self.compass_texture = Texture()

        # Initialize compass HUD element
        self.compassHUD = OnscreenImage(image=self.compass_texture, pos=(1.4, 0, -0.55), scale=0.5)
        self.compassHUD.setTransparency(True)

        # Set the initial zoom level
        self.zoom = 200

    def update(self, aircrafts_pos, aircrafts_hpr, velocity, ground_height):
        """
        Updates the HUD elements, minimap, and compass based on the current state of the aircraft.
        """
        ground_height = 0 if ground_height is None else ground_height
        
        # Update the height HUD with the current height of the aircraft
        heightHUD_text = f'{aircrafts_pos[0].z - ground_height:.0f}'
        self.heightHUD.setText(heightHUD_text)

        # Update the velocity HUD with the current velocity of the aircraft
        velocityHUD_text = f'{velocity.length():.0f}'
        self.velocityHUD.setText(velocityHUD_text)

        # Calculate the coordinates of the center of the minimap
        x = int((aircrafts_pos[0].x + (408400/2)) * (13056/408400))
        y = int((aircrafts_pos[0].y + (233000/2)) * (7424/233000))

        # Adjust the center coordinates based on the zoom level and the size of the map
        if x - self.zoom < 0:
            self.center_x = self.zoom
        elif x + self.zoom > self.map_img.shape[1]:
            self.center_x = self.map_img.shape[1] - self.zoom
        else:
            self.center_x = x

        if y - self.zoom < 0:
            self.center_y = self.zoom
        elif y + self.zoom > self.map_img.shape[0]:
            self.center_y = self.map_img.shape[0] - self.zoom
        else:
            self.center_y = y

        # Extract the minimap image centered around the current position of the aircraft
        crop_img = np.copy(self.map_img[self.center_y-self.zoom:self.center_y+self.zoom, self.center_x-self.zoom:self.center_x+self.zoom])

        # Loop through all the aircrafts and add them to the minimap image
        for aircraft_pos, aircraft_hpr in zip(aircrafts_pos, aircrafts_hpr):
            # Calculate the position of the aircraft relative to the center of the minimap
            x_offset = int((aircraft_pos.x + (408400/2)) * (13056/408400)) - (self.center_x - self.zoom)
            y_offset = int((aircraft_pos.y + (233000/2)) * (7424/233000)) - (self.center_y - self.zoom)

            # Rotate the aircraft icon to match its heading
            rotated_aircraft_icon = imutils.rotate(self.aircraft_icon_img, -aircraft_hpr[0])

            # Calculate the offsets for the aircraft icon
            y_offset_start = y_offset - (rotated_aircraft_icon.shape[0] // 2)
            y_offset_end = y_offset + (rotated_aircraft_icon.shape[0] // 2)
            x_offset_start = x_offset - (rotated_aircraft_icon.shape[1] // 2)
            x_offset_end = x_offset + (rotated_aircraft_icon.shape[1] // 2)

            # Blend the aircraft icon with the minimap image
            alpha_s = rotated_aircraft_icon[:, :, 3] / 255.0
            alpha_l = 1.0 - alpha_s

            try:
                for c in range(0, 3):
                    crop_img[y_offset_start:y_offset_end, x_offset_start:x_offset_end, c] = (alpha_s * rotated_aircraft_icon[:, :, c] +
                                                                                            alpha_l * crop_img[y_offset_start:y_offset_end, x_offset_start:x_offset_end, c])
            except:
                # out of border
                pass
        
        # Rotate the image
        crop_img = imutils.rotate(crop_img, aircrafts_hpr[0][0])

        # Create a circular mask with same shape as input
        circle_mask = np.zeros_like(crop_img)
        circle_mask = cv2.circle(circle_mask, (crop_img.shape[0] // 2, crop_img.shape[1] // 2), self.zoom, (255,255,255), -1)

        # Convert the image to BGRA format and add the circle mask to alpha channel
        crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2BGRA)
        crop_img[:, :, 3] = circle_mask[:,:,0]

        # Convert the image to a NumPy array
        crop_img = np.array(crop_img)

        # Setup a 2D texture for minimap, set the image and transparency
        self.minimap_texture.setup2dTexture(crop_img.shape[0], crop_img.shape[1],  Texture.T_unsigned_byte, Texture.F_rgba)
        self.minimap_texture.setRamImage(crop_img)
        self.minimapHUD.setImage(self.minimap_texture)
        self.minimapHUD.setTransparency(True)

        # Rotate the compass image
        true_compass = imutils.rotate(self.compass_img, aircrafts_hpr[0][0])

        # Setup a 2D texture for compass, set the image and transparency
        self.compass_texture.setup2dTexture(true_compass.shape[0], true_compass.shape[1],  Texture.T_unsigned_byte, Texture.F_rgba)
        self.compass_texture.setRamImage(true_compass)
        self.compassHUD.setImage(self.compass_texture)
        self.compassHUD.setTransparency(True)
    
    def zoom_in(self) -> None:
        """Decrease zoom level by 5, with a minimum of 100."""
        if self.zoom > 100:
            self.zoom -= 5

    def zoom_out(self) -> None:
        """Increase zoom level by 5, with a maximum of 400."""
        if self.zoom < 400:
            self.zoom += 5

    def cleanup(self) -> None:
        """Destroy all Heads-Up Display (HUD) objects."""
        self.headingHUD.destroy()
        self.heightHUD.destroy()
        self.minimapHUD.destroy()
        self.compassHUD.destroy()
        self.velocityHUD.destroy()
