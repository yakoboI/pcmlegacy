"""
Image Optimizer Utility
Converts images to WebP format with high quality settings for clean, crisp images
"""

import os
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Quality settings - HD Quality for clean, crisp images
WEBP_QUALITY = 92  # HD Quality (90-95 recommended, 92 for HD standard)
JPEG_QUALITY = 95  # High quality JPEG fallback
PNG_COMPRESSION = 6  # PNG compression level (0-9, 6 is balanced)

# HD Quality Standards
HD_MIN_WIDTH = 1280  # Minimum width for HD (720p)
HD_MIN_HEIGHT = 720  # Minimum height for HD (720p)
FULL_HD_WIDTH = 1920  # Full HD width (1080p)
FULL_HD_HEIGHT = 1080  # Full HD height (1080p)

# Image size limits for responsive images (HD optimized)
RESPONSIVE_SIZES = {
    'thumbnail': (200, 200),
    'small': (400, 400),
    'medium': (800, 800),
    'hd': (1280, 720),  # HD (720p)
    'large': (1920, 1080),  # Full HD (1080p)
    'xlarge': (2560, 1440)  # 2K (1440p)
}


def optimize_image(input_path, output_path=None, format='webp', quality=WEBP_QUALITY, 
                  max_size=None, sharpen=False, preserve_transparency=True, maintain_hd=True):
    """
    Optimize an image to WebP format with HD quality settings
    
    Args:
        input_path: Path to input image
        output_path: Path to output image (optional, auto-generated if None)
        format: Output format ('webp', 'jpeg', 'png')
        quality: Quality setting (90-95 for HD images, default 92)
        max_size: Tuple (width, height) for maximum size
        sharpen: Apply subtle sharpening for crisp HD images
        preserve_transparency: Preserve alpha channel for PNG
        maintain_hd: Ensure HD quality standards are met
    
    Returns:
        Path to optimized image
    """
    try:
        # Open image
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if saving as JPEG
            if format.lower() == 'jpeg' and img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Ensure RGB mode for WebP
            if format.lower() == 'webp' and img.mode not in ('RGB', 'RGBA'):
                if img.mode == 'P' and preserve_transparency:
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            
            # Resize if max_size specified (maintain aspect ratio)
            if max_size:
                # Use LANCZOS resampling for best quality (HD standard)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Ensure HD quality if maintain_hd is True
                if maintain_hd and format.lower() == 'webp':
                    width, height = img.size
                    # Warn if image is below HD standards
                    if width < HD_MIN_WIDTH or height < HD_MIN_HEIGHT:
                        logger.warning(f"Image {input_path} is below HD standards: {width}x{height}")
            
            # Ensure minimum quality for HD
            if maintain_hd and quality < 90:
                quality = 90  # Minimum quality for HD
            
            # Apply HD-quality sharpening for crisp images
            if sharpen or maintain_hd:
                # Use unsharp mask optimized for HD quality
                # Higher radius and percent for HD images
                img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=3))
            
            # Enhance image quality for HD
            enhancer = ImageEnhance.Sharpness(img)
            if maintain_hd:
                img = enhancer.enhance(1.08)  # Enhanced sharpening for HD (8% increase)
            else:
                img = enhancer.enhance(1.05)  # Standard sharpening (5% increase)
            
            # Generate output path if not provided
            if output_path is None:
                base_path = Path(input_path)
                output_path = base_path.parent / f"{base_path.stem}.{format.lower()}"
            
            # Save with high quality settings
            save_kwargs = {
                'optimize': True,
                'quality': quality
            }
            
            if format.lower() == 'webp':
                # HD Quality WebP settings
                save_kwargs.update({
                    'method': 6,  # Best compression method (slower but best quality for HD)
                    'lossless': False,  # Use lossy for smaller files
                    'quality': quality,  # HD quality (92 default)
                    'exact': False  # Allow color space conversion for better quality
                })
                if img.mode == 'RGBA' and preserve_transparency:
                    save_kwargs['lossless'] = False  # Still use lossy but preserve alpha
                    save_kwargs['exact'] = True  # Preserve exact colors for transparency
            elif format.lower() == 'jpeg':
                save_kwargs.update({
                    'quality': quality,
                    'progressive': True,  # Progressive JPEG for better loading
                    'optimize': True
                })
            elif format.lower() == 'png':
                save_kwargs.update({
                    'compress_level': PNG_COMPRESSION,
                    'optimize': True
                })
            
            # Save optimized image
            img.save(output_path, format=format.upper(), **save_kwargs)
            
            logger.info(f"Optimized image: {input_path} -> {output_path} ({format.upper()}, quality: {quality})")
            return str(output_path)
            
    except Exception as e:
        logger.error(f"Error optimizing image {input_path}: {e}")
        raise


def generate_responsive_images(input_path, output_dir=None, base_name=None):
    """
    Generate responsive image sizes in WebP format
    
    Args:
        input_path: Path to source image
        output_dir: Output directory (optional)
        base_name: Base name for output files (optional)
    
    Returns:
        Dictionary of size names to file paths
    """
    try:
        source_path = Path(input_path)
        
        if output_dir is None:
            output_dir = source_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        if base_name is None:
            base_name = source_path.stem
        
        responsive_images = {}
        
        # Generate each size
        for size_name, max_size in RESPONSIVE_SIZES.items():
            output_path = output_dir / f"{base_name}_{size_name}.webp"
            
            # Only resize if source is larger than target
            with Image.open(input_path) as img:
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    optimize_image(
                        input_path,
                        output_path,
                        format='webp',
                        quality=WEBP_QUALITY,
                        max_size=max_size,
                        sharpen=True  # Sharpen resized images
                    )
                    responsive_images[size_name] = str(output_path)
                else:
                    # Use original if smaller than target
                    optimize_image(
                        input_path,
                        output_path,
                        format='webp',
                        quality=WEBP_QUALITY,
                        sharpen=False  # No need to sharpen if not resizing
                    )
                    responsive_images[size_name] = str(output_path)
        
        return responsive_images
        
    except Exception as e:
        logger.error(f"Error generating responsive images for {input_path}: {e}")
        raise


def convert_to_webp(input_path, output_path=None, quality=WEBP_QUALITY, 
                    preserve_original=True, sharpen=True, maintain_hd=True):
    """
    Convert image to WebP format with HD quality
    
    Args:
        input_path: Path to input image
        output_path: Path to output WebP (optional)
        quality: WebP quality (90-95 for HD, default 92)
        preserve_original: Keep original file
        sharpen: Apply sharpening for crisp HD images (default True)
        maintain_hd: Ensure HD quality standards (default True)
    
    Returns:
        Path to WebP file
    """
    try:
        source_path = Path(input_path)
        
        if output_path is None:
            output_path = source_path.parent / f"{source_path.stem}.webp"
        else:
            output_path = Path(output_path)
        
        # Optimize to WebP with HD quality
        optimize_image(
            input_path,
            output_path,
            format='webp',
            quality=quality,
            sharpen=sharpen,
            preserve_transparency=True,
            maintain_hd=maintain_hd
        )
        
        # Remove original if not preserving
        if not preserve_original and source_path.exists():
            source_path.unlink()
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error converting {input_path} to WebP: {e}")
        raise


def get_image_info(image_path):
    """
    Get image information including HD quality check
    
    Returns:
        Dictionary with image metadata and HD quality status
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            is_hd = width >= HD_MIN_WIDTH and height >= HD_MIN_HEIGHT
            is_full_hd = width >= FULL_HD_WIDTH and height >= FULL_HD_HEIGHT
            
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': width,
                'height': height,
                'has_transparency': img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info,
                'is_hd': is_hd,
                'is_full_hd': is_full_hd,
                'hd_standard': 'Full HD (1080p)' if is_full_hd else ('HD (720p)' if is_hd else 'Below HD')
            }
    except Exception as e:
        logger.error(f"Error getting image info for {image_path}: {e}")
        return None


def ensure_hd_quality(image_path, min_width=HD_MIN_WIDTH, min_height=HD_MIN_HEIGHT):
    """
    Check if image meets HD quality standards
    
    Args:
        image_path: Path to image
        min_width: Minimum width for HD (default 1280)
        min_height: Minimum height for HD (default 720)
    
    Returns:
        Tuple (is_hd, width, height, recommendation)
    """
    info = get_image_info(image_path)
    if not info:
        return False, 0, 0, "Invalid image"
    
    width = info['width']
    height = info['height']
    is_hd = width >= min_width and height >= min_height
    
    if not is_hd:
        recommendation = f"Image is {width}x{height}. HD requires at least {min_width}x{min_height}"
    elif width >= FULL_HD_WIDTH and height >= FULL_HD_HEIGHT:
        recommendation = "Image meets Full HD (1080p) standards"
    else:
        recommendation = "Image meets HD (720p) standards"
    
    return is_hd, width, height, recommendation


def is_webp_supported():
    """
    Check if WebP format is supported
    """
    try:
        # Try to create a small WebP image
        test_img = Image.new('RGB', (1, 1), color='red')
        test_path = Path('/tmp/test_webp.webp')
        test_img.save(test_path, 'WEBP')
        test_path.unlink()
        return True
    except:
        return False

