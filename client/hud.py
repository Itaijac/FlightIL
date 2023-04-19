from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import TextNode
from panda3d.core import Texture
from panda3d.core import CullBinManager

import numpy as np
import cv2
import imutils

from constants import MAP

class HUD:
    def __init__(self, aircraft_pos):
        self.heightHUD = OnscreenText(text="0",
                                      pos=(0.675, 0.025),
                                      scale=0.05,
                                      fg=(70, 192, 22, 255),
                                      mayChange=True,
                                      align=TextNode.ARight)

        self.velocityHUD = OnscreenText(text="0",
                                        pos=(-0.675, 0.025),
                                        scale=0.05,
                                        fg=(70, 192, 22, 255),
                                        mayChange=True,
                                        align=TextNode.ALeft)

        self.headingHUD = OnscreenImage(image="models/HUD/heading.png",
                                        pos=(0, 0, 0),
                                        scale=(0.8, 0.1, 0.1))
        self.headingHUD.setTransparency(True)

        self.map_img = cv2.imread(f"models/enviorment/{MAP}/GOOGLE_SAT_WM.tif", cv2.IMREAD_UNCHANGED)
        self.map_img = cv2.flip(self.map_img, 0)

        self.aircraft_icon_img = cv2.imread(f"models/HUD/f16-icon.png", cv2.IMREAD_UNCHANGED)
        self.aircraft_icon_img = cv2.flip(self.aircraft_icon_img, 0)

        self.minimap_texture = Texture()

        self.minimapHUD = OnscreenImage(image=self.minimap_texture,
                                        pos=(1.3, 0, -0.55),
                                        scale=0.4)

        self.zoom = 200

    def update(self, aircrafts_pos, aircrafts_hpr, velocity):
        heightHUD_text = f'{aircrafts_pos[0].z:.0f}'
        self.heightHUD.setText(heightHUD_text)

        velocityHUD_text = f'{velocity.length():.0f}'
        self.velocityHUD.setText(velocityHUD_text)

        x = int((aircrafts_pos[0].x + 34_244)/38.21875)
        y = int((aircrafts_pos[0].y + 24_460)/38.21875)
        
        if x - self.zoom < 0:
            self.center_x = self.zoom
        elif x + self.zoom > 1792:
            self.center_x = 1792 - self.zoom
        else:
            self.center_x = x

        if y - self.zoom < 0:
            self.center_y = self.zoom
        elif y + self.zoom > 1280:
            self.center_y = 1280 - self.zoom
        else:
            self.center_y = y

        crop_img = np.copy(self.map_img)

        for aircraft_pos, aircraft_hpr in zip(aircrafts_pos, aircrafts_hpr):
            # Add aircrafts to crop_img
            x_offset = int((aircraft_pos.x + 34_244)/38.21875)
            y_offset = int((aircraft_pos.y + 24_460)/38.21875)

            # Rotate aircraft
            rotated_aircraft_icon = imutils.rotate(self.aircraft_icon_img, -aircraft_hpr[0])

            # Calculate offsets
            y_offset_start = y_offset - (rotated_aircraft_icon.shape[0] // 2)
            y_offset_end = y_offset + (rotated_aircraft_icon.shape[0] // 2)
            x_offset_start = x_offset - (rotated_aircraft_icon.shape[1] // 2)
            x_offset_end = x_offset + (rotated_aircraft_icon.shape[1] // 2)

            alpha_s = rotated_aircraft_icon[:, :, 3] / 255.0
            alpha_l = 1.0 - alpha_s

            try:
                # Update crop_img
                for c in range(0, 3):
                    crop_img[y_offset_start:y_offset_end, x_offset_start:x_offset_end, c] = (alpha_s * rotated_aircraft_icon[:, :, c] +
                                            alpha_l * crop_img[y_offset_start:y_offset_end, x_offset_start:x_offset_end, c])
            except:
                # out of border
                pass
        
        crop_img = crop_img[self.center_y-self.zoom:self.center_y+self.zoom, self.center_x-self.zoom:self.center_x+self.zoom]
        crop_img = imutils.rotate(crop_img, aircrafts_hpr[0][0])

        circle_mask = np.zeros_like(crop_img)
        circle_mask = cv2.circle(circle_mask, (crop_img.shape[0] // 2, crop_img.shape[1] // 2), self.zoom, (255,255,255), -1)

        # put mask into alpha channel of input
        crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2BGRA)
        crop_img[:, :, 3] = circle_mask[:,:,0]

        crop_img = np.array(crop_img)

        self.minimap_texture.setup2dTexture(crop_img.shape[0], crop_img.shape[1],  Texture.T_unsigned_byte, Texture.F_rgba)
        self.minimap_texture.setRamImage(crop_img)
        self.minimapHUD.setImage(self.minimap_texture)
        self.minimapHUD.setTransparency(True)
    
    def zoom_in(self):
        if self.zoom > 100:
            self.zoom -= 5

    def zoom_out(self):
        if self.zoom < 400:
            self.zoom += 5

    def cleanup(self):
        self.headingHUD.destroy()
        self.heightHUD.destroy()
        self.minimapHUD.destroy()
        self.velocityHUD.destroy()
