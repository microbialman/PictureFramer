import os
import random
import time
from itertools import cycle
from PIL import Image
from pillow_heif import register_heif_opener
import screeninfo
import pygame
import io

# Register HEIF format
register_heif_opener()

# Define color palette
COLOR_PALETTE = [(255, 99, 71), (135, 206, 250), (240, 230, 140), (152, 251, 152), (216, 191, 216)]
BORDER_WIDTH = 10
TRANSITION_SPEED = 20

def get_image_info(folder_path):
    image_info = {}
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path) and filename.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff', 'heic')):
            with Image.open(file_path) as img:
                width, height = img.size
                orientation = "Portrait" if height > width else "Landscape"
                image_info[file_path] = {"width": width, "height": height, "orientation": orientation}
    
    return image_info

def get_display_resolution():
    screen = screeninfo.get_monitors()[0]
    return {"width": screen.width, "height": screen.height}

def load_image_compatible(img_path):
    """Convert image to a Pygame-compatible format if necessary."""
    with Image.open(img_path) as img:
        img = img.convert("RGBA")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")  # Convert to PNG for compatibility
        img_bytes.seek(0)
        return pygame.image.load(img_bytes, "temp.png")

def slide_transition(screen, layout, direction_out=True):
    """Slides images/squares out (or in) from the center."""
    steps = TRANSITION_SPEED
    for step in range(steps + 1):
        screen.fill((0, 0, 0))
        progress = step / steps if direction_out else (1 - step / steps)
        
        for pos in layout:
            x, y = pos["position"]
            w, h = pos["size"]
            if not (isinstance(w, (int, float)) and isinstance(h, (int, float))):
                continue  # Skip invalid sizes
            
            offset = int(progress * max(w, h))
            new_x = x + (w // 2 - offset if direction_out else offset - w // 2)
            new_y = y + (h // 2 - offset if direction_out else offset - h // 2)
            
            pygame.draw.rect(screen, (0, 0, 0), (new_x, new_y, w, h))
        
        pygame.display.flip()
        pygame.time.delay(20)

def display_slideshow(image_info, display_resolution, interval=3):
    pygame.init()
    screen = pygame.display.set_mode((display_resolution["width"], display_resolution["height"]), pygame.FULLSCREEN)
    pygame.display.set_caption("Image Slideshow")
    clock = pygame.time.Clock()
    images = list(image_info.keys())
    random.shuffle(images)
    
    while True:
        layout = random.choice(get_layouts(display_resolution))
        selected_images = random.sample(images, min(len(images), len(layout)))
        num_replacements = random.randint(0, min(2, len(layout)))
        replace_indices = random.sample(range(len(layout)), num_replacements)
        
        slide_transition(screen, layout, direction_out=True)
        screen.fill((0, 0, 0))  # Black background
        
        for i, pos in enumerate(layout):
            if i in replace_indices:
                color = random.choice(COLOR_PALETTE)
                pygame.draw.rect(screen, color, (*pos["position"], *pos["size"]))
            else:
                img = load_image_compatible(selected_images.pop())
                img = scale_and_crop(img, pos["size"])  # Maintain aspect ratio with cropping
                img_rect = img.get_rect(center=(pos["position"][0] + pos["size"][0] // 2, 
                                                pos["position"][1] + pos["size"][1] // 2))
                screen.blit(img, img_rect.topleft)
            pygame.draw.rect(screen, (0, 0, 0), (*pos["position"], *pos["size"]), BORDER_WIDTH)  # Black borders
        
        pygame.display.flip()
        slide_transition(screen, layout, direction_out=False)
        
        start_time = time.time()
        while time.time() - start_time < interval:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
            clock.tick(60)

def scale_and_crop(image, target_size):
    """Scales the image to fill the target size while maintaining aspect ratio and cropping excess."""
    if not (isinstance(target_size, tuple) and len(target_size) == 2):
        raise ValueError("Size must be a tuple of two numbers (width, height)")
    
    img_w, img_h = image.get_size()
    target_w, target_h = target_size
    
    scale = max(target_w / img_w, target_h / img_h)
    new_size = (int(img_w * scale), int(img_h * scale))
    
    image = pygame.transform.scale(image, new_size)
    
    crop_x = max(0, (new_size[0] - target_w) // 2)
    crop_y = max(0, (new_size[1] - target_h) // 2)
    crop_w = min(target_w, new_size[0])
    crop_h = min(target_h, new_size[1])
    
    img_rect = pygame.Rect(crop_x, crop_y, crop_w, crop_h)
    
    return image.subsurface(img_rect).copy()

def get_layouts(display_resolution):
    """Returns predefined layouts for image arrangement."""
    width, height = display_resolution["width"], display_resolution["height"]
    return [
        [{"position": (width // 3 * i, 0), "size": (width // 3, height)} for i in range(3)],
        [{"position": (0, 0), "size": (width, height)}],
        [{"position": (x * width // 2, y * height // 2), "size": (width // 2, height // 2)} for y in range(2) for x in range(2)],
        [{"position": (0, 0), "size": (width // 3, height)},
         {"position": (width // 3, 0), "size": (2 * width // 3, height // 2)},
         {"position": (width // 3, height // 2), "size": (2 * width // 3, height // 2)}],
        [{"position": (0, 0), "size": (2 * width // 3, height // 2)},
         {"position": (0, height // 2), "size": (2 * width // 3, height // 2)},
         {"position": (2 * width // 3, 0), "size": (width // 3, height)}]
    ]

# Example usage
folder_path = "Images"
image_data = get_image_info(folder_path)
display_resolution = get_display_resolution()
display_slideshow(image_data, display_resolution)
