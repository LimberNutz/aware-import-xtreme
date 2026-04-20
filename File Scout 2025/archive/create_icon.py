"""
File Scout Icon Generator
Creates a simple icon file for the application.
"""

from PIL import Image, ImageDraw, ImageFont
import sys

def create_icon(output_path="filescout.ico"):
    """Create a simple magnifying glass icon for File Scout."""
    
    # Create base image (256x256 for high quality)
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    blue = (74, 144, 226, 255)  # Primary color
    white = (255, 255, 255, 255)
    
    # Draw magnifying glass
    center_x, center_y = size // 2, size // 2 - 20
    radius = 70
    
    # Outer circle (glass rim)
    draw.ellipse(
        [center_x - radius - 8, center_y - radius - 8,
         center_x + radius + 8, center_y + radius + 8],
        fill=blue
    )
    
    # Inner circle (glass)
    draw.ellipse(
        [center_x - radius, center_y - radius,
         center_x + radius, center_y + radius],
        fill=(230, 240, 255, 255)  # Light blue glass
    )
    
    # Handle
    handle_start_x = center_x + int(radius * 0.7)
    handle_start_y = center_y + int(radius * 0.7)
    handle_end_x = center_x + int(radius * 1.8)
    handle_end_y = center_y + int(radius * 1.8)
    
    # Draw handle (thick line)
    draw.line(
        [handle_start_x, handle_start_y, handle_end_x, handle_end_y],
        fill=blue,
        width=25
    )
    
    # Add "F" letter in the glass
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    # Draw "F"
    text = "F"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center_x - text_width // 2
    text_y = center_y - text_height // 2 - 5
    
    draw.text((text_x, text_y), text, fill=blue, font=font)
    
    # Create multi-resolution icon
    # Windows .ico files contain multiple sizes
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    icons = []
    for icon_size in icon_sizes:
        resized = img.resize(icon_size, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # Save as .ico file
    icons[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in icons],
        append_images=icons[1:]
    )
    
    print(f"✓ Icon created: {output_path}")
    print(f"  Sizes included: {', '.join([f'{w}x{h}' for w, h in icon_sizes])}")
    return output_path

def create_png_icon(output_path="filescout.png"):
    """Create a PNG version of the icon for the system tray."""
    
    # Create base image (64x64 for tray icon)
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    blue = (74, 144, 226, 255)
    
    # Draw magnifying glass
    center_x, center_y = size // 2, size // 2 - 5
    radius = 18
    
    # Outer circle (glass rim)
    draw.ellipse(
        [center_x - radius - 2, center_y - radius - 2,
         center_x + radius + 2, center_y + radius + 2],
        fill=blue
    )
    
    # Inner circle (glass)
    draw.ellipse(
        [center_x - radius, center_y - radius,
         center_x + radius, center_y + radius],
        fill=(230, 240, 255, 255)
    )
    
    # Handle
    handle_start_x = center_x + int(radius * 0.7)
    handle_start_y = center_y + int(radius * 0.7)
    handle_end_x = center_x + int(radius * 1.8)
    handle_end_y = center_y + int(radius * 1.8)
    
    draw.line(
        [handle_start_x, handle_start_y, handle_end_x, handle_end_y],
        fill=blue,
        width=6
    )
    
    # Add "F"
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    text = "F"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center_x - text_width // 2
    text_y = center_y - text_height // 2 - 1
    
    draw.text((text_x, text_y), text, fill=blue, font=font)
    
    img.save(output_path, format='PNG')
    print(f"✓ PNG icon created: {output_path}")
    return output_path

if __name__ == "__main__":
    print("File Scout Icon Generator")
    print("-" * 50)
    
    try:
        # Create both .ico and .png versions
        ico_path = create_icon("filescout.ico")
        png_path = create_png_icon("filescout.png")
        
        print("\n" + "=" * 50)
        print("Icons created successfully!")
        print("=" * 50)
        print("\nUsage:")
        print(f"  • {ico_path} - Use for PyInstaller --icon option")
        print(f"  • {png_path} - Use for system tray icon")
        print("\nPyInstaller command:")
        print(f'  pyinstaller --icon="{ico_path}" --windowed --onefile "File Scout 3.2.py"')
        
    except Exception as e:
        print(f"\n❌ Error creating icons: {e}")
        print("\nMake sure you have Pillow installed:")
        print("  pip install Pillow")
        sys.exit(1)
