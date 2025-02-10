#version 0.1

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import random
import time
from PIL import Image, ExifTags
import screeninfo
import pygame
import io
import math
import sys

#Color palette if option to have squares is chosen
COLOR_PALETTES = {
    "Mondrian":[
    (243, 243, 242),
    (175, 54, 60),
    (56, 61, 150),
    (231, 199, 31)],
    "70s":[
        (63,138,140),
        (12,86,121),
        (11,8,53),
        (229,52,11),
        (242,138,15),
        (255,231,189)
    ]
}

DISPLAY_TIME = 2
SQUARES = True
PALETTE = "Mondrian"
BORDER_WIDTH = 10
ANIMATION_SPEED = 20
TICK_SPEED = 60
FULLSCREEN = True

class ImageObject:
    #setup image
    def __init__(self, img, target_pos, target_size, swid, shei, is_color_square=False, color=None):
        self.img = img
        #coorindate to end up at
        self.target_pos = target_pos
        #size in layout
        self.target_size = target_size
        #store screen size
        self.screendim = (swid, shei)
        #add a slight random speed adjustment to add variety
        self.speed_adj = random.uniform(0.8,1.1)
        # set inital position off screen in a horizontal or vertical direciton
        direction = random.choice(["left", "right", "up", "down"])
        if direction == "left":
            self.current_pos = (-self.screendim[0], self.target_pos[1])
        elif direction == "right":
            self.current_pos = (self.screendim[0], self.target_pos[1])
        elif direction == "up":
            self.current_pos = (self.target_pos[0], -self.screendim[1])
        else:
            self.current_pos = (self.target_pos[0], self.screendim[1])
            
        self.is_color_square = is_color_square
        self.color = color
        #check if image is where it should end up
        self.done = False

    #function to set outward transition positions
    def setout(self):
        #re adjust speed
        self.speed_adj = random.uniform(0.8,1.1)
        self.done = False
        # set outside position off screen in a horizontal or vertical direciton
        direction = random.choice(["left", "right", "up", "down"])
        if direction == "left":
            self.target_pos = (-self.screendim[0], self.current_pos[1])
        elif direction == "right":
            self.target_pos = (self.screendim[0], self.current_pos[1])
        elif direction == "up":
            self.target_pos = (self.current_pos[0], -self.screendim[1])
        else:
            self.target_pos = (self.current_pos[0], self.screendim[1])
        
    #move if not where it should be
    def update(self):
        if not self.done:
            cx, cy = self.current_pos
            tx, ty = self.target_pos
            new_x = cx + (tx - cx) / (ANIMATION_SPEED * self.speed_adj)
            new_y = cy + (ty - cy) / (ANIMATION_SPEED * self.speed_adj)
            self.current_pos = (new_x, new_y)
            if abs(tx - new_x) < 1 and abs(ty - new_y) < 1:
                self.current_pos = self.target_pos
                self.done = True
                
    #render photo or coloured square
    def draw(self, screen):
        pos = (int(self.current_pos[0]), int(self.current_pos[1]))
        if self.is_color_square:
            pygame.draw.rect(screen, self.color, (pos[0], pos[1], self.target_size[0], self.target_size[1]))
        else:
            #scale and crop to maintain aspect ratio
            scaled_img = scale_and_crop(self.img, self.target_size)
            img_rect = scaled_img.get_rect(center=(pos[0] + self.target_size[0] // 2, 
                                                    pos[1] + self.target_size[1] // 2))
            screen.blit(scaled_img, img_rect.topleft)
        #add border
        pygame.draw.rect(screen, (0, 0, 0), (pos[0], pos[1], self.target_size[0], self.target_size[1]), BORDER_WIDTH)
            
#store initial info on images for layout creation
def get_image_info(folder_path):
    image_info = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(
            ('png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff')):
            img = Image.open(file_path)
            width, height = img.size
            image_info[file_path] = {
                    "width": width,
                    "height": height,
                    "orientation": "Portrait" if height > width else "Landscape"
                }
    return image_info

#screen size
def get_display_resolution():
    mon = screeninfo.get_monitors()[0]
    return {"width": mon.width, "height": mon.height}

#for overly large images dont skew dimensions just focus on center of image
def scale_and_crop(image, target_size):
    img_w, img_h = image.get_size()
    target_w, target_h = target_size
    scale = max(target_w / img_w, target_h / img_h)
    new_size = (math.ceil(img_w * scale), math.ceil(img_h * scale))
    image = pygame.transform.smoothscale(image, new_size)
    # Compute centered crop rectangle of exactly target_size.
    crop_x = (new_size[0] - target_w) // 2
    crop_y = (new_size[1] - target_h) // 2
    # Clamp crop values to ensure the rectangle is within bounds.
    crop_x = max(0, min(crop_x, new_size[0] - target_w))
    crop_y = max(0, min(crop_y, new_size[1] - target_h))
    crop_rect = pygame.Rect(crop_x, crop_y, target_w, target_h)
    return image.subsurface(crop_rect).copy()

#pygame handling prevent not responding, handle exit
def pyg_handle(clock):
    pygame.event.pump()
    clock.tick(TICK_SPEED)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sys.exit()

#run the slideshow
def display_slideshow(image_info, display_resolution, interval=3, fullscreen=False, squares=True):
    pygame.init()
    pygame.mouse.set_visible(False)
    # Set the screen size and windowed or not
    #pull the screen width and height
    swidth = display_resolution["width"]
    sheight = display_resolution["height"]
    
    if fullscreen:
        screen = pygame.display.set_mode((swidth, sheight), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((swidth, sheight))
    pygame.display.set_caption("PhotoRotato")
    #clock to set fps
    clock = pygame.time.Clock()
    #get the file paths for randomisation across layouts
    images = list(image_info.keys())
    random.shuffle(images)

    running = True
    
    #loop to run the slideshow
    while running:
        #get the layout
        layout = random.choice(get_layouts(display_resolution))
        objects = []

        #get images for the layout
        selected_images = random.sample(images, min(len(images), len(layout)))
        #if squares is on on replace some photos with coloured squares, ensure there is always at least image
        num_replacements = 0
        if squares:
            num_replacements = random.randint(0, len(layout) - 1 )
        replace_indices = random.sample(range(len(layout)), num_replacements)

        #add the coloured squares or images
        for i, pos in enumerate(layout):
            if i in replace_indices:
                color = random.choice(COLOR_PALETTES[PALETTE])
                objects.append(ImageObject(None, pos["position"], pos["size"], swidth, sheight, is_color_square=True, color=color))
            else:
                img = pygame.image.load(selected_images.pop())
                objects.append(ImageObject(img, pos["position"], pos["size"], swidth, sheight))

        #animate objects from their random start positions to their layout positions
        while not all(obj.done for obj in objects):
            screen.fill((0, 0, 0))
            for obj in objects:
                obj.update()
                obj.draw(screen)
            pygame.display.flip()
            pyg_handle(clock)

        #hold the current layout for the interval
        hold_start = time.time()
        while time.time() - hold_start < interval:
            pyg_handle(clock)

        #set new target positions for transition out
        for obj in objects:
            obj.setout()
            
        #animate transition out
        while not all(obj.done for obj in objects):
            screen.fill((0, 0, 0))
            for obj in objects:
                obj.update()
                obj.draw(screen)
            pygame.display.flip()
            pyg_handle(clock)
            
#specify possible layouts
def get_layouts(display_resolution):
    width, height = display_resolution["width"], display_resolution["height"]
    return [
        [{"position": (width // 3 * i, 0), "size": (width // 3, height)} for i in range(3)],
        [{"position": (0, 0), "size": (width, height)}],
        [{"position": (x * width // 2, y * height // 2), "size": (width // 2, height // 2)} for y in range(2) for x in range(2)]
    ]

folder_path = "Images"
image_data = get_image_info(folder_path)
display_resolution = get_display_resolution()
display_slideshow(image_data, display_resolution, interval=DISPLAY_TIME, fullscreen=FULLSCREEN, squares=SQUARES)
