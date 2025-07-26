#!/usr/bin/env python3
"""
Create simple icons for the browser extension
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_extension_icon(size, filename):
    """Create a simple shield icon with 'A' letter"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors - green theme
    bg_color = (36, 250, 57)  # Green #24fa39
    text_color = (255, 255, 255)  # White
    border_color = (0, 0, 0)  # Black
    
    # Draw shield shape
    margin = size // 8
    shield_points = [
        (size//2, margin),  # Top center
        (size - margin, margin + size//4),  # Top right
        (size - margin, size - margin - size//4),  # Bottom right
        (size//2, size - margin),  # Bottom center
        (margin, size - margin - size//4),  # Bottom left
        (margin, margin + size//4),  # Top left
    ]
    
    # Draw shield background
    draw.polygon(shield_points, fill=bg_color, outline=border_color, width=2)
    
    # Draw letter 'A' in the center
    try:
        font_size = size // 2
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text size and position
    text = "A"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - size // 16
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

def main():
    """Create all required icon sizes"""
    icons_dir = "/app/browser-extension/icons"
    
    # Create icon sizes required by manifest
    sizes = [16, 32, 48, 128]
    
    for size in sizes:
        filename = f"{icons_dir}/icon{size}.png"
        create_extension_icon(size, filename)
    
    print("✅ All browser extension icons created successfully!")

if __name__ == "__main__":
    main()