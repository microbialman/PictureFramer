import os
import random
import time
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
import screeninfo
import pygame
import io

# Register HEIF format
register_heif_opener()

# Define color palette and parameters
COLOR_PALETTE = [
    (255, 99, 71),
    (135, 206, 250),
    (240, 230, 140),
    (152, 251, 152),
    (216, 191, 216)
]
BORDER_WIDTH = 10
ANIMATION_SPEED = 15

class ImageObject:
    def __init__(self, img, target_pos, target_size, is_color_square=False, color=None):
        self.img = img
        self.target_pos = target_pos            # Final destination (tuple of ints)
        self.target_size = target_size          # (width, height)
        # Use floats for smooth interpolation.
        self.current_pos = (float(random.randint(0, 1920)), float(random.randint(0, 1080)))
        self.is_color_square = is_color_square
        self.color = color
        self.done = False
    
    def update(self):
        if not self.done:
            cx, cy = self.current_pos
            tx, ty = self.target_pos
            # Use float arithmetic for smooth movement.
            new_x = cx + (tx - cx) / ANIMATION_SPEED
            new_y = cy + (ty - cy) / ANIMATION_SPEED
            self.current_pos = (new_x, new_y)
            if abs(tx - new_x) < 1 and abs(ty - new_y) < 1:
                self.current_pos = self.target_pos
                self.done = True
    
    def draw(self, screen):
        pos = (int(self.current_pos[0]), int(self.current_pos[1]))
        if self.is_color_square:
            pygame.draw.rect(screen, self.color, (pos[0], pos[1], self.target_size[0], self.target_size[1]))
        else:
            # Scale and crop to maintain aspect ratio.
            scaled_img = scale_and_crop(self.img, self.target_size)
            img_rect = scaled_img.get_rect(center=(pos[0] + self.target_size[0] // 2, 
                                                    pos[1] + self.target_size[1] // 2))
            screen.blit(scaled_img, img_rect.topleft)
        # Always draw a border.
        pygame.draw.rect(screen, (0, 0, 0), (pos[0], pos[1], self.target_size[0], self.target_size[1]), BORDER_WIDTH)

def get_image_info(folder_path):
    image_info = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(
            ('png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff', 'heic')):
            with Image.open(file_path) as img:
                exif = img.getexif()
                if exif is not None:
                    orientation = exif.get(274, 1)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
                width, height = img.size
                image_info[file_path] = {
                    "width": width,
                    "height": height,
                    "orientation": "Portrait" if height > width else "Landscape"
                }
    return image_info

def get_display_resolution():
    mon = screeninfo.get_monitors()[0]
    return {"width": mon.width, "height": mon.height}

def load_image_compatible(img_path):
    with Image.open(img_path) as img:
        img = img.convert("RGBA")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return pygame.image.load(img_bytes, "temp.png")

def scale_and_crop(image, target_size):
    """Scale image to fill target_size while maintaining aspect ratio, then center-crop."""
    img_w, img_h = image.get_size()
    target_w, target_h = target_size
    scale = max(target_w / img_w, target_h / img_h)
    new_size = (int(img_w * scale), int(img_h * scale))
    image = pygame.transform.smoothscale(image, new_size)
    # Compute centered crop rectangle of exactly target_size.
    crop_x = (new_size[0] - target_w) // 2
    crop_y = (new_size[1] - target_h) // 2
    # Clamp crop values to ensure the rectangle is within bounds.
    crop_x = max(0, min(crop_x, new_size[0] - target_w))
    crop_y = max(0, min(crop_y, new_size[1] - target_h))
    crop_rect = pygame.Rect(crop_x, crop_y, target_w, target_h)
    return image.subsurface(crop_rect).copy()

def display_slideshow(image_info, display_resolution, interval=3):
    pygame.init()
    # Set the screen with size tuple and FULLSCREEN flag.
    screen = pygame.display.set_mode((int(display_resolution["width"]), int(display_resolution["height"])), pygame.FULLSCREEN)
    pygame.display.set_caption("Image Slideshow")
    clock = pygame.time.Clock()
    images = list(image_info.keys())
    random.shuffle(images)
    next_layout = random.choice(get_layouts(display_resolution))

    while True:
        current_layout = next_layout
        next_layout = random.choice(get_layouts(display_resolution))
        objects = []
        # If layout has one slot, force a photo.
        if len(current_layout) == 1:
            selected_images = random.sample(images, 1)
            num_replacements = 0
            replace_indices = []
        else:
            selected_images = random.sample(images, min(len(images), len(current_layout)))
            num_replacements = random.randint(0, min(2, len(current_layout)))
            replace_indices = random.sample(range(len(current_layout)), num_replacements)

        for i, pos in enumerate(current_layout):
            if i in replace_indices:
                color = random.choice(COLOR_PALETTE)
                objects.append(ImageObject(None, pos["position"], pos["size"], is_color_square=True, color=color))
            else:
                img = load_image_compatible(selected_images.pop())
                objects.append(ImageObject(img, pos["position"], pos["size"]))

        # Animate transition in: objects move from their random start positions to their layout positions.
        while not all(obj.done for obj in objects):
            screen.fill((0, 0, 0))
            for obj in objects:
                obj.update()
                obj.draw(screen)
            pygame.display.flip()
            clock.tick(60)

        # Hold the current layout for the interval (using a responsive loop)
        hold_start = time.time()
        while time.time() - hold_start < interval:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
            clock.tick(60)

        # Set new target positions for transition out:
        width = display_resolution["width"]
        height = display_resolution["height"]
        for obj in objects:
            obj.done = False
            # Choose a horizontal or vertical move (no diagonal)
            direction = random.choice(["left", "right", "up", "down"])
            if direction == "left":
                obj.target_pos = (-width, obj.current_pos[1])
            elif direction == "right":
                obj.target_pos = (width, obj.current_pos[1])
            elif direction == "up":
                obj.target_pos = (obj.current_pos[0], -height)
            else:  # down
                obj.target_pos = (obj.current_pos[0], height)

        # Animate transition out (objects move off-screen) with no extra delay.
        while not all(obj.done for obj in objects):
            screen.fill((0, 0, 0))
            for obj in objects:
                obj.update()
                obj.draw(screen)
            pygame.display.flip()
            clock.tick(60)
        # Immediately proceed to the next layout.
        
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
display_slideshow(image_data, display_resolution)
