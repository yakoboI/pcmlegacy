#!/usr/bin/env python3
"""
Image Conversion Script
Converts existing images to WebP format with high quality settings
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.image_optimizer import (
        convert_to_webp, 
        get_image_info, 
        ensure_hd_quality,
        WEBP_QUALITY,
        HD_MIN_WIDTH,
        HD_MIN_HEIGHT
    )
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    print("Error: Image optimization not available. Install Pillow: pip install Pillow")
    sys.exit(1)


def convert_directory_images(directory, recursive=True, preserve_original=True):
    """
    Convert all images in a directory to WebP
    
    Args:
        directory: Directory path to process
        recursive: Process subdirectories
        preserve_original: Keep original files
    """
    directory = Path(directory)
    
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        return
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    converted_count = 0
    skipped_count = 0
    error_count = 0
    
    # Get all image files
    if recursive:
        image_files = []
        for ext in image_extensions:
            image_files.extend(directory.rglob(f'*{ext}'))
            image_files.extend(directory.rglob(f'*{ext.upper()}'))
    else:
        image_files = []
        for ext in image_extensions:
            image_files.extend(directory.glob(f'*{ext}'))
            image_files.extend(directory.glob(f'*{ext.upper()}'))
    
    print(f"\nFound {len(image_files)} image files to process...\n")
    
    for image_file in image_files:
        try:
            # Skip if WebP already exists
            webp_path = image_file.with_suffix('.webp')
            if webp_path.exists():
                print(f"⏭️  Skipping {image_file.name} (WebP already exists)")
                skipped_count += 1
                continue
            
            # Get image info
            info = get_image_info(str(image_file))
            if not info:
                print(f"⚠️  Skipping {image_file.name} (invalid image)")
                skipped_count += 1
                continue
            
            # Check HD quality
            is_hd, width, height, hd_status = ensure_hd_quality(str(image_file))
            hd_indicator = "✅ HD" if is_hd else "⚠️  Below HD"
            
            print(f"🔄 Converting {image_file.name} ({info['width']}x{info['height']}, {info['format']}) {hd_indicator}...")
            
            # Convert to WebP with HD quality
            convert_to_webp(
                str(image_file),
                str(webp_path),
                quality=WEBP_QUALITY,
                preserve_original=preserve_original,
                sharpen=True,  # Sharpen for crisp HD images
                maintain_hd=True  # Ensure HD quality standards
            )
            
            # Get file sizes
            original_size = image_file.stat().st_size
            webp_size = webp_path.stat().st_size
            reduction = ((original_size - webp_size) / original_size) * 100
            
            print(f"   ✅ Created {webp_path.name} ({reduction:.1f}% smaller)")
            converted_count += 1
            
        except Exception as e:
            print(f"   ❌ Error converting {image_file.name}: {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"  ✅ Converted: {converted_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"{'='*60}\n")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python convert_images.py <directory> [--no-recursive] [--delete-originals]")
        print("\nExample:")
        print("  python convert_images.py static/uploads/images")
        print("  python convert_images.py static/uploads/images --no-recursive")
        print("  python convert_images.py static/uploads/images --delete-originals")
        sys.exit(1)
    
    directory = sys.argv[1]
    recursive = '--no-recursive' not in sys.argv
    preserve_original = '--delete-originals' not in sys.argv
    
    if not preserve_original:
        response = input("⚠️  WARNING: This will delete original images. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    print(f"\n{'='*60}")
    print(f"Image Conversion to WebP")
    print(f"{'='*60}")
    print(f"Directory: {directory}")
    print(f"Recursive: {recursive}")
    print(f"Preserve Originals: {preserve_original}")
    print(f"Quality: {WEBP_QUALITY} (HD Quality for clean, crisp images)")
    print(f"HD Standard: Minimum {HD_MIN_WIDTH}x{HD_MIN_HEIGHT} (720p)")
    print(f"{'='*60}\n")
    
    convert_directory_images(directory, recursive=recursive, preserve_original=preserve_original)


if __name__ == '__main__':
    main()

