#version 0.1

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import random
import time
from PIL import Image
import screeninfo
import pygame
import math
import sys
import cv2

#Color palette if option to have squares is chosen
COLOR_PALETTES = {
    "Mondrian":[
    (243, 243, 242),
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

DISPLAY_TIME = 3
#set to "All" for only coloured squares, "Some" for a mix of photos and squares, "None" for only photos
SQUARES = "Some"
PALETTE = "Mondrian"
BORDER_WIDTH = 10
ANIMATION_SPEED = 15
TICK_SPEED = 30
#if on initialisation will be slower as faces are detected in each image to center cropping
FACEDETECT = False
FULLSCREEN = True

FACEMODEL = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

class ImageObject:
    #setup image
    def __init__(self, img, target_pos, target_size, swid, shei, focus, is_color_square=False, color=None):
        #load and trim the image
        if is_color_square == False:
            self.img = scale_and_crop(img, target_size, focus)
        #coorindate to end up at
        self.target_pos = target_pos
        #size in layout
        self.target_size = target_size
        #store screen size
        self.screendim = (swid, shei)
        #add a slight random speed adjustment to add variety
        self.speed_adj = random.uniform(0.8,1.2)
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
            screen.blit(self.img, (pos[0], pos[1], self.target_size[0], self.target_size[1]))
        #add border
        pygame.draw.rect(screen, (0, 0, 0), (pos[0], pos[1], self.target_size[0], self.target_size[1]), BORDER_WIDTH)

#function to ID faces in an image
def find_faces(file, fm=FACEMODEL):
    img = cv2.imread(file)
    resizer = 0.3
    if img.shape[0] and  img.shape[1] <1000:
        resizer = 1
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_img = cv2.resize(gray_img, (0,0), fx=resizer, fy=resizer)  
    face = fm.detectMultiScale(
        gray_img,  minNeighbors=4)
    #return mean vector
    if len(face)>0:
            x_mean = int(sum(x+(w/2) for x, y,  w, h in face) / len(face))
            y_mean = int(sum(y+(h/2) for x, y,  w, h in face) / len(face))
            x_mean = x_mean * (1/resizer)
            y_mean = y_mean * (1/resizer)
            return(x_mean,y_mean)
    else:
        return(False)
            
        
#store initial info on images for layout creation, try to detect faces to find a region to focus on
def get_image_info(folder_path, F=False):
    print("Loading images...")
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
                    "orientation": "Portrait" if height > width else "Landscape",
                    "focus": find_faces(file_path) if F==True else False
                }
    return image_info

#screen size
def get_display_resolution():
    mon = screeninfo.get_monitors()[0]
    return {"width": mon.width, "height": mon.height}

#for overly large images dont skew dimensions just focus on center of image
def scale_and_crop(image, target_size, focus):
    img_w, img_h = image.get_size()
    target_w, target_h = target_size
    scale = max(target_w / img_w, target_h / img_h)
    new_size = (math.ceil(img_w * scale), math.ceil(img_h * scale))
    image = pygame.transform.smoothscale(image, new_size)
    #if no faces center on the middle
    if focus == False:
        # Compute centered crop rectangle of exactly target_size
        crop_x = (new_size[0] - target_w) // 2
        crop_y = (new_size[1] - target_h) // 2
    else:
        focusper = (focus[0] // img_w , focus[1] // img_h)
        focusadj = (new_size[0]*focusper[0], new_size[1]*focusper[1])
        crop_x = focusadj[0] - (target_w // 2)
        crop_y = focusadj[1] - (target_h // 2)
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
def display_slideshow(image_info, display_resolution, interval=3, fullscreen=False, squares="Some"):
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

    #load the layouts
    layouts = get_layouts(display_resolution, laylis)
    
    running = True
    
    #loop to run the slideshow
    print("Starting slideshow...")
    while running:
        #get the layout
        layout = random.choice(layouts)
        objects = []

        #get images for the layout
        selected_images = random.sample(images, min(len(images), len(layout)))
            
        #if squares is on on replace some photos with coloured squares, ensure there is always at least image
        num_replacements = 0
        if squares == "Some":
            num_replacements = random.randint(0, len(layout) - 1 )
        elif squares == "All":
            num_replacements = len(layout)
        replace_indices = random.sample(range(len(layout)), num_replacements)

        #add the coloured squares or images
        for i, pos in enumerate(layout):
            if i in replace_indices:
                color = random.choice(COLOR_PALETTES[PALETTE])
                objects.append(ImageObject(None, pos["p"], pos["s"], swidth, sheight, False, is_color_square=True, color=color))
            else:
                ipath = selected_images.pop()
                img = pygame.image.load(ipath)
                objects.append(ImageObject(img, pos["p"], pos["s"], swidth, sheight, image_info[ipath]["focus"]))

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
def get_layouts(display_resolution, laylis):
    width, height = display_resolution["width"], display_resolution["height"]
    for i in laylis:
        for j in i:
            j["p"][0] = j["p"][0] * width
            j["p"][1] = j["p"][1] * height
            j["s"][0] = j["s"][0] * width
            j["s"][1] = j["s"][1] * height
    return laylis

#list with possible layouts, p gives top left position (x,y) , s gives size (w,h) , all values are fractions of total screen
laylis = [
    [{"p":[0,0],"s":[1,1]}],
    [{"p":[0,0],"s":[1,1]}],
    [{"p":[0,0],"s":[1,1]}],
    [{"p":[0,0],"s":[0.4,1]}, {"p":[0.4,0],"s":[0.6,0.5]}, {"p":[0.4,0.5],"s":[0.6,0.5]}],
    [{"p":[0,0],"s":[0.6,0.5]}, {"p":[0,0.5],"s":[0.6,0.5]}, {"p":[0.6,0],"s":[0.4,1]}],
    [{"p":[0,0],"s":[0.5,0.5]},{"p":[0.5,0],"s":[0.5,0.5]},{"p":[0,0.5],"s":[0.5,0.5]},{"p":[0.5,0.5],"s":[0.5,0.5]}],
    [{"p":[0,0],"s":[0.4,0.5]},{"p":[0,0.5],"s":[0.4,0.5]},{"p":[0.4,0],"s":[0.3,1]},{"p":[0.7,0],"s":[0.3,1]}],
    [{"p":[0,0],"s":[0.3,1]},{"p":[0.3,0],"s":[0.3,1]},{"p":[0.6,0],"s":[0.4,0.5]},{"p":[0.6,0.5],"s":[0.4,0.5]}],
    [{"p":[0,0],"s":[0.333,1]},{"p":[0.333,0],"s":[0.333,1]},{"p":[0.666,0],"s":[0.333,1]}],
    [{"p":[0,0],"s":[0.3,1]},{"p":[0.3,0],"s":[0.4,0.5]},{"p":[0.3,0.5],"s":[0.4,0.5]},{"p":[0.7,0],"s":[0.3,1]}],
    [{"p":[0,0],"s":[0.3,0.5]},{"p":[0,0.5],"s":[0.3,0.5]},{"p":[0.3,0],"s":[0.4,1]},{"p":[0.7,0],"s":[0.3,0.5]},{"p":[0.7,0.5],"s":[0.3,0.5]}],
    [{"p":[0,0],"s":[0.7,1]},{"p":[0.7,0],"s":[0.3,0.4]},{"p":[0.7,0.4],"s":[0.3,0.6]}],
    [{"p":[0,0],"s":[0.3,0.6]},{"p":[0,0.6],"s":[0.3,0.4]},{"p":[0.3,0],"s":[0.7,1]}],
    [{"p":[0,0],"s":[0.25,1]},{"p":[0.25,0],"s":[0.5,1]},{"p":[0.75,0],"s":[0.25,1]}],
    [{"p":[0,0],"s":[0.5,0.5]},{"p":[0,0.5],"s":[0.5,0.5]},{"p":[0.5,0],"s":[0.5,1]}],
    [{"p":[0,0],"s":[0.5,1]},{"p":[0.5,0],"s":[0.5,0.5]},{"p":[0.5,0.5],"s":[0.5,0.5]}],
    [{"p":[0,0],"s":[0.4,0.333]},{"p":[0,0.333],"s":[0.4,0.333]},{"p":[0,0.666],"s":[0.4,0.333]},{"p":[0.4,0],"s":[0.6,1]}],
    [{"p":[0,0],"s":[0.6,1]},{"p":[0.6,0],"s":[0.4,0.333]},{"p":[0.6,0.333],"s":[0.4,0.333]},{"p":[0.6,0.666],"s":[0.4,0.333]}],
    [{"p":[0,0],"s":[0.6,0.6]},{"p":[0,0.6],"s":[0.3,0.4]},{"p":[0.3,0.6],"s":[0.3,0.4]},{"p":[0.6,0],"s":[0.4,0.3]},{"p":[0.6,0.3],"s":[0.4,0.7]}]
]

folder_path = "Images"
image_data = get_image_info(folder_path, F=FACEDETECT)
display_resolution = get_display_resolution()
display_slideshow(image_data, display_resolution, interval=DISPLAY_TIME, fullscreen=FULLSCREEN, squares=SQUARES)
