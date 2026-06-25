import random
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw
from scripts.config import SPLITS_DIR, REPORTS_DIR, TARGET_IMAGES_PER_CLASS, RANDOM_SEED
from scripts.utils import load_image, save_image

# -------------------------------------------------
# Approach 1: Standard Augmentations
# -------------------------------------------------

def apply_rotation(img, angle=None):
    """Rotates the image by a random angle."""
    if angle is None:
        angle = random.uniform(-15, 15)
    return img.rotate(angle, Image.Resampling.BILINEAR, expand=False, fillcolor=(0, 0, 0))

def apply_flip(img, p=0.5):
    """Flips the image horizontally with probability p."""
    if random.random() < p:
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    return img

def apply_brightness(img, factor=None):
    """Adjusts the image brightness."""
    if factor is None:
        factor = random.uniform(0.8, 1.2)
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)

def apply_contrast(img, factor=None):
    """Adjusts the image contrast."""
    if factor is None:
        factor = random.uniform(0.8, 1.2)
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)

def apply_gamma(img, gamma=None):
    """Applies gamma correction to the image."""
    if gamma is None:
        gamma = random.uniform(0.7, 1.3)
    # Create a lookup table (LUT)
    inv_gamma = 1.0 / gamma
    lut = [int(((i / 255.0) ** inv_gamma) * 255) for i in range(256)]
    # If RGB, apply to each channel
    if img.mode == "RGB":
        return img.point(lut * 3)
    return img.point(lut)

def apply_gaussian_noise(img, std=None):
    """Adds random Gaussian noise to the image."""
    if std is None:
        std = random.uniform(5, 15)
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, std, arr.shape)
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_arr)

def apply_perspective(img, translate=None, shear=None):
    """Applies a random affine perspective translation and shear."""
    if translate is None:
        translate = (random.uniform(-10, 10), random.uniform(-10, 10))
    if shear is None:
        shear = random.uniform(-5, 5)
    # In Pillow, we can use rotate with translation and shear
    return img.rotate(0, Image.Resampling.BILINEAR, translate=translate, shear=shear, fillcolor=(0, 0, 0))

def apply_crop(img, crop_factor=None):
    """Crops the image randomly and resizes it back to original size."""
    if crop_factor is None:
        crop_factor = random.uniform(0.9, 1.0)
    w, h = img.size
    new_w = int(w * crop_factor)
    new_h = int(h * crop_factor)
    x = random.randint(0, w - new_w)
    y = random.randint(0, h - new_h)
    cropped = img.crop((x, y, x + new_w, y + new_h))
    return cropped.resize((w, h), Image.Resampling.LANCZOS)

def apply_blur(img, radius=None):
    """Applies random blur to the image."""
    if radius is None:
        radius = random.uniform(0.5, 1.5)
    return img.filter(ImageFilter.GaussianBlur(radius))

def apply_equalize(img):
    """Applies histogram equalization (CLAHE equivalent)."""
    return ImageOps.equalize(img)

# -------------------------------------------------
# Approach 2: Controlled Railway Defect Simulation
# -------------------------------------------------

def add_rust_texture(img, opacity=None):
    """
    Simulates rust by generating a brownish-red textured noise overlay
    and blending it with the original track image.
    """
    if opacity is None:
        opacity = random.uniform(0.12, 0.28)
        
    w, h = img.size
    # Create a low-res noise texture and upscale it to get smooth blotches
    noise_w, noise_h = 32, 32
    noise_arr = np.random.uniform(0, 255, (noise_h, noise_w)).astype(np.uint8)
    noise_img = Image.fromarray(noise_arr).resize((w, h), Image.Resampling.BILINEAR)
    noise_filtered = noise_img.filter(ImageFilter.GaussianBlur(radius=5))
    noise_arr_full = np.array(noise_filtered, dtype=np.float32) / 255.0
    
    # Define rust colors (brownish-red / orange-brown)
    rust_r = 145 + np.random.normal(0, 10, (h, w))
    rust_g = 75 + np.random.normal(0, 8, (h, w))
    rust_b = 30 + np.random.normal(0, 5, (h, w))
    rust_rgb = np.stack([rust_r, rust_g, rust_b], axis=-1)
    rust_rgb = np.clip(rust_rgb, 0, 255).astype(np.uint8)
    rust_img = Image.fromarray(rust_rgb)
    
    # Create mask using the noise pattern
    mask_arr = (noise_arr_full * 255 * opacity).astype(np.uint8)
    mask_img = Image.fromarray(mask_arr)
    
    return Image.composite(rust_img, img, mask_img)

def add_surface_wear(img, width=None):
    """
    Simulates a shiny wheel contact band (surface wear glare) on the rail head
    by drawing a bright vertical band with blurred borders in the center.
    """
    if width is None:
        width = random.randint(15, 30)
        
    w, h = img.size
    overlay = img.copy()
    draw = ImageDraw.Draw(overlay)
    
    # We assume the rail is running vertically in the center.
    # We draw a bright band down the middle.
    center_x = w // 2 + random.randint(-15, 15)
    x_start = center_x - width // 2
    x_end = center_x + width // 2
    
    # Draw polished shiny steel band
    draw.rectangle([x_start, 0, x_end, h], fill=(245, 245, 250))
    
    # Blur the overlay and blend it to make it look like a smooth, reflective rail surface
    overlay_blurred = overlay.filter(ImageFilter.GaussianBlur(radius=3))
    
    # Use alpha mask to blend the bright track surface smoothly
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    # Smooth gradient mask for the band
    for i in range(width):
        col_x = x_start + i
        if 0 <= col_x < w:
            # parabolic transparency profile
            alpha = int(90 * (1 - ((i - width/2) / (width/2))**2))
            mask_draw.line([col_x, 0, col_x, h], fill=alpha)
            
    return Image.composite(overlay_blurred, img, mask)

def add_crack_extension(img, crack_length=None):
    """
    Simulates a small crack extension by drawing a thin, dark, jagged path
    representing a crack.
    """
    if crack_length is None:
        crack_length = random.randint(10, 25)
        
    w, h = img.size
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Start near the center or a random coordinate where defects are visible
    start_x = w // 2 + random.randint(-30, 30)
    start_y = h // 2 + random.randint(-40, 40)
    
    curr_x, curr_y = start_x, start_y
    for _ in range(crack_length):
        # Draw a line segment
        next_x = curr_x + random.randint(-4, 4)
        next_y = curr_y + random.randint(2, 6) # extend downwards with small horizontal deviations
        
        # Clip coordinates
        next_x = max(0, min(w - 1, next_x))
        next_y = max(0, min(h - 1, next_y))
        
        # Draw dark gray crack segment
        draw.line([curr_x, curr_y, next_x, next_y], fill=(20, 20, 20), width=random.randint(1, 2))
        curr_x, curr_y = next_x, next_y
        
    return img_copy

def add_rain(img, intensity=None):
    """Simulates rain streaks on the camera lens / environment."""
    if intensity is None:
        intensity = random.randint(30, 60)
        
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for _ in range(intensity):
        length = random.randint(10, 25)
        angle_x = random.randint(-4, 4)
        
        x = random.randint(0, w)
        y = random.randint(0, h)
        
        alpha = random.randint(30, 80)
        draw.line([x, y, x + angle_x, y + length], fill=(255, 255, 255, alpha), width=1)
        
    img_rgba = img.convert("RGBA")
    blended = Image.alpha_composite(img_rgba, overlay)
    return blended.convert("RGB")

def add_fog(img, opacity=None):
    """Simulates foggy/misty weather conditions."""
    if opacity is None:
        opacity = random.uniform(0.15, 0.35)
        
    w, h = img.size
    fog_overlay = Image.new("RGB", (w, h), (230, 230, 235))
    return Image.blend(img, fog_overlay, opacity)

def add_shadow(img):
    """Simulates realistic lighting shadows across the tracks."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Create a random shadow polygon
    # cover a corner or side of the image
    p_type = random.choice(["top", "left", "right"])
    alpha = random.randint(40, 110)
    
    if p_type == "top":
        draw.polygon([(0, 0), (w, 0), (random.randint(w//2, w), random.randint(h//4, h//2)), (0, random.randint(h//4, h//2))], fill=(0, 0, 0, alpha))
    elif p_type == "left":
        draw.polygon([(0, 0), (random.randint(w//4, w//2), 0), (random.randint(w//4, w//2), h), (0, h)], fill=(0, 0, 0, alpha))
    else:
        draw.polygon([(random.randint(w//2, w*3//4), 0), (w, 0), (w, h), (random.randint(w//2, w*3//4), h)], fill=(0, 0, 0, alpha))
        
    img_rgba = img.convert("RGBA")
    blended = Image.alpha_composite(img_rgba, overlay)
    
    # Blur the shadow border slightly for soft shadow
    shadow_rgb = blended.convert("RGB")
    return Image.blend(img, shadow_rgb, 0.9)

def add_dust(img, count=None):
    """Draws tiny dark specs on the image to simulate lens dust."""
    if count is None:
        count = random.randint(5, 12)
        
    w, h = img.size
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    
    for _ in range(count):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        r = random.choice([1, 2])
        alpha = random.randint(50, 150)
        
        # Draw small dust dot
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(40, 38, 35))
        
    return img_copy

def apply_lighting_variation(img, factor=None):
    """Adjusts local/global lighting exposure to simulate sunset, glare, etc."""
    if factor is None:
        factor = random.choice([0.65, 0.75, 1.25, 1.35]) # dark vs bright exposure
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


# -------------------------------------------------
# Orchestrated Generator
# -------------------------------------------------

def generate_synthetic_data(split_counts):
    """
    Calculates class imbalances and automatically generates synthetic images.
    Target capacity: 250 images per class in total (real + synthetic).
    Synthetic images are generated ONLY from real training images.
    Synthetic images are saved in dataset/splits/train/[class_name]/
    Logs each generation in reports/augmentation_log.csv.
    """
    print("\n[Step 4] Class Balancing & Synthetic Data Generation...")
    
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    augmentation_log = []
    total_synthetic_generated = 0
    
    for class_name, counts in split_counts.items():
        total_real = counts["total_real"]
        train_real_count = counts["train_real"]
        
        # How many synthetic images are needed to reach TARGET_IMAGES_PER_CLASS (250)?
        needed_synthetic = TARGET_IMAGES_PER_CLASS - total_real
        
        if needed_synthetic <= 0:
            print(f"Class '{class_name}' is already balanced (total real={total_real} >= {TARGET_IMAGES_PER_CLASS}). Skipping synthetic generation.")
            continue
            
        print(f"Class '{class_name}': total real={total_real} | train real={train_real_count}. Generating {needed_synthetic} synthetic images...")
        
        # Load the paths of real training images
        class_train_dir = SPLITS_DIR / "train" / class_name
        real_train_files = sorted([f for f in class_train_dir.iterdir() if f.is_file() and not f.name.startswith("synthetic_")])
        
        if len(real_train_files) == 0:
            print(f"WARNING: No training files found for class '{class_name}' to augment! Skipping.")
            continue
            
        for i in range(1, needed_synthetic + 1):
            # 1. Pick a random source real image
            src_file = random.choice(real_train_files)
            img = load_image(src_file)
            
            # 2. Decide approach
            # 50% Standard Augmentations, 50% Defect Simulations, or combination
            approach_roll = random.random()
            
            applied_ops = []
            
            if approach_roll < 0.35:
                # Approach 1: Pure Standard Augmentation
                approach = "Standard Augmentation"
                # Apply rotation
                img = apply_rotation(img)
                applied_ops.append("Rotation")
                # Flip
                if random.random() < 0.5:
                    img = apply_flip(img)
                    applied_ops.append("Horizontal Flip")
                # Contrast/Brightness
                if random.random() < 0.5:
                    img = apply_brightness(img)
                    applied_ops.append("Brightness Adjustment")
                if random.random() < 0.5:
                    img = apply_contrast(img)
                    applied_ops.append("Contrast Adjustment")
                # Blur or equalization
                if random.random() < 0.3:
                    img = apply_blur(img)
                    applied_ops.append("Gaussian Blur")
                if random.random() < 0.3:
                    img = apply_equalize(img)
                    applied_ops.append("Histogram Equalization")
                    
            elif approach_roll < 0.70:
                # Approach 2: Controlled Railway Defect Simulation
                approach = "Railway Defect Simulation"
                
                # Apply class-specific variations and general weather/camera anomalies
                defect_roll = random.random()
                
                # Rust
                if random.random() < 0.4:
                    img = add_rust_texture(img)
                    applied_ops.append("Rust Texture")
                    
                # Defect lines
                if class_name in ["crack", "broken_rail"] and random.random() < 0.6:
                    img = add_crack_extension(img)
                    applied_ops.append("Crack Extension")
                elif class_name == "surface_wear" and random.random() < 0.6:
                    img = add_surface_wear(img)
                    applied_ops.append("Surface Wear Contact Band")
                    
                # Weather variations
                weather_roll = random.random()
                if weather_roll < 0.3:
                    img = add_rain(img)
                    applied_ops.append("Rain Weather Overlay")
                elif weather_roll < 0.6:
                    img = add_fog(img)
                    applied_ops.append("Fog Weather Overlay")
                    
                # Shadows/Dust
                if random.random() < 0.4:
                    img = add_shadow(img)
                    applied_ops.append("Shadow Simulation")
                if random.random() < 0.3:
                    img = add_dust(img)
                    applied_ops.append("Lens Dust Spec")
                    
            else:
                # Combined Approach
                approach = "Combined"
                
                # Standard
                img = apply_rotation(img)
                applied_ops.append("Rotation")
                if random.random() < 0.5:
                    img = apply_flip(img)
                    applied_ops.append("Horizontal Flip")
                
                # Anomaly
                sim_choice = random.choice(["rust", "wear", "crack", "weather", "shadow"])
                if sim_choice == "rust":
                    img = add_rust_texture(img)
                    applied_ops.append("Rust Texture")
                elif sim_choice == "wear" and class_name == "surface_wear":
                    img = add_surface_wear(img)
                    applied_ops.append("Surface Wear Contact Band")
                elif sim_choice == "crack" and class_name in ["crack", "broken_rail"]:
                    img = add_crack_extension(img)
                    applied_ops.append("Crack Extension")
                elif sim_choice == "weather":
                    if random.random() < 0.5:
                        img = add_rain(img)
                        applied_ops.append("Rain Weather Overlay")
                    else:
                        img = add_fog(img)
                        applied_ops.append("Fog Weather Overlay")
                elif sim_choice == "shadow":
                    img = add_shadow(img)
                    applied_ops.append("Shadow Simulation")
                    
                # Global brightness
                img = apply_lighting_variation(img)
                applied_ops.append("Lighting Variation")
                
            # 3. Save synthetic image
            synthetic_filename = f"synthetic_{class_name}_{i:04d}.jpg"
            dest_path = class_train_dir / synthetic_filename
            save_image(img, dest_path, format="JPEG")
            
            # 4. Log
            augmentation_log.append({
                "synthetic_image_name": synthetic_filename,
                "source_image_name": src_file.name,
                "class": class_name,
                "approach": approach,
                "parameters_used": ", ".join(applied_ops)
            })
            
            total_synthetic_generated += 1
            
        print(f"Class '{class_name}' balancing complete. Total count in training set = {train_real_count + needed_synthetic} ({train_real_count} real + {needed_synthetic} synthetic).")

    # Save log to CSV
    log_df = pd.DataFrame(augmentation_log)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = REPORTS_DIR / "augmentation_log.csv"
    log_df.to_csv(log_path, index=False)
    
    print(f"\nSynthetic generation completed. Generated {total_synthetic_generated} images. Log saved to:\n{log_path}")
    return augmentation_log
