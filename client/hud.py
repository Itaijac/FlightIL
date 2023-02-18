from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import TextNode
from panda3d.core import Texture
from panda3d.core import CullBinManager

import numpy as np
import cv2

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

        self.img = cv2.imread(f"models/enviorment/{MAP}/GOOGLE_SAT_WM.tif")
        self.img = cv2.flip(self.img, 0)

        m = 200
        x = int(aircraft_pos[0]/38.21875)
        y = int(aircraft_pos[1]/38.21875)
        if y-m < 0:
            y = m
        if x-m < 0:
            x = m
        crop_img = self.img[y-m:y+m, x-m:x+m]
        crop_img = np.array(crop_img)

        self.minimap_texture = Texture()
        self.minimap_texture.setup2dTexture(crop_img.shape[0], crop_img.shape[1],  Texture.T_unsigned_byte, Texture.F_rgb)
        self.minimap_texture.setRamImage(crop_img)
        self.minimapHUD = OnscreenImage(image=self.minimap_texture,
                                        pos=(1.3, 0, -0.55),
                                        scale=0.3)
        
        self.minimap_iconHUD = OnscreenImage(image="models/HUD/minimap_icon.png",
                                             pos=(1.3, 0, -0.55),
                                             scale=0.04)
        self.minimap_iconHUD.setTransparency(True)

        self.minimap_overlayHUD = OnscreenImage(image="models/HUD/minimap_overlay.png",
                                        pos=(1.3, 0, -0.55),
                                        scale=0.35)
        self.minimap_overlayHUD.setTransparency(True)

        cullManager = CullBinManager.getGlobalPtr()
        cullManager.addBin("onscreenImageBin", cullManager.BTFixed, 60)
        self.minimap_iconHUD.setBin("onscreenImageBin", 1)
        self.minimap_overlayHUD.setBin("onscreenImageBin", 2)
        self.minimapHUD.setBin("onscreenImageBin", 3)

    def update(self, aircraft_pos, aircraft_hpr, velocity):
        heightHUD_text = f'{aircraft_pos.z:.0f}'
        self.heightHUD.setText(heightHUD_text)

        velocityHUD_text = f'{velocity.length():.0f}'
        self.velocityHUD.setText(velocityHUD_text)

        m = 200
        x = int((aircraft_pos.x + 34_244)/38.21875)
        y = int((aircraft_pos.y + 24_460)/38.21875)
        if x - m < 0:
            center_x = m
        elif x + m > 1792:
            center_x = 1792 - m
        else:
            center_x = x

        if y - m < 0:
            center_y = m
        elif y + m > 1280:
            center_y = 1280 - m
        else:
            center_y = y
            
        crop_img = self.img[center_y-m:center_y+m, center_x-m:center_x+m]
        crop_img = np.array(crop_img)

        self.minimap_texture.setup2dTexture(crop_img.shape[0], crop_img.shape[1],  Texture.T_unsigned_byte, Texture.F_rgb)
        self.minimap_texture.setRamImage(crop_img)
        self.minimapHUD.setImage(self.minimap_texture)
        
        icon_x = self.minimapHUD.getX() + (x-center_x)/(2*m)*self.minimapHUD.getSx()
        icon_z = self.minimapHUD.getZ() + (y-center_y)/(2*m)*self.minimapHUD.getSx()
        self.minimap_iconHUD.setPos(icon_x, 0, icon_z)
        self.minimap_iconHUD.setR(-aircraft_hpr[0])

    def change_map_scale(self):
        pass

    def __del__(self):
        self.headingHUD.destroy()
        self.heightHUD.destroy()
        self.minimapHUD.destroy()
        self.minimap_iconHUD.destroy()
        self.velocityHUD.destroy()