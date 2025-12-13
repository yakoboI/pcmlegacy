#!/usr/bin/env python3
"""
Production Build Script
Minifies CSS and JavaScript files for production deployment
"""

import os
import sys
import re
from pathlib import Path

# Try to import minification libraries
try:
    import cssmin
    CSSMIN_AVAILABLE = True
except ImportError:
    CSSMIN_AVAILABLE = False
    print("Warning: cssmin not installed. CSS minification will use basic method.")
    print("Install with: pip install cssmin")

try:
    import jsmin
    JSMIN_AVAILABLE = True
except ImportError:
    JSMIN_AVAILABLE = False
    print("Warning: jsmin not installed. JavaScript minification will use basic method.")
    print("Install with: pip install jsmin")


def basic_css_minify(css_content):
    """Basic CSS minification without external library"""
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    # Remove extra whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    # Remove whitespace around certain characters
    css_content = re.sub(r'\s*([{}:;,])\s*', r'\1', css_content)
    # Remove trailing semicolons
    css_content = re.sub(r';}', '}', css_content)
    return css_content.strip()


def basic_js_minify(js_content):
    """Basic JavaScript minification without external library"""
    # Remove single-line comments (but not URLs)
    js_content = re.sub(r'(?<!:)\/\/.*', '', js_content)
    # Remove multi-line comments
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    # Remove extra whitespace
    js_content = re.sub(r'\s+', ' ', js_content)
    # Remove whitespace around operators (but be careful)
    js_content = re.sub(r'\s*([=+\-*/%<>!&|,;:{}()\[\]])\s*', r'\1', js_content)
    return js_content.strip()


def minify_file(input_path, output_path, file_type):
    """Minify a single file"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if file_type == 'css':
            if CSSMIN_AVAILABLE:
                minified = cssmin.cssmin(content)
            else:
                minified = basic_css_minify(content)
        elif file_type == 'js':
            if JSMIN_AVAILABLE:
                minified = jsmin.jsmin(content)
            else:
                minified = basic_js_minify(content)
        else:
            print(f"Unknown file type: {file_type}")
            return False
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write minified content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        # Calculate compression ratio
        original_size = len(content)
        minified_size = len(minified)
        compression = ((original_size - minified_size) / original_size) * 100
        
        print(f"✓ {input_path.name} → {output_path.name} ({compression:.1f}% reduction)")
        return True
        
    except Exception as e:
        print(f"✗ Error minifying {input_path}: {e}")
        return False


def build_production_assets():
    """Build production assets"""
    print("Building production assets...\n")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    static_dir = project_root / 'static'
    
    # Files to minify
    css_files = [
        'css/style.css',
        'css/badges.css',
        'css/cookie-consent.css',
        'css/loading.css',
    ]
    
    js_files = [
        'js/polyfills.js',
        'js/main.js',
        'js/accessibility.js',
        'js/form-validation.js',
        'js/interactions.js',
        'js/safe-dom.js',
        'js/error-handler.js',
        'js/payment-handler.js',
        'js/docx-viewer.js',
        'js/admin-interactions.js',
        'js/dashboard-tabs.js',
        'js/cookie-consent.js',
        'js/loading-states.js',
    ]
    
    success_count = 0
    total_count = len(css_files) + len(js_files)
    
    # Minify CSS files
    print("Minifying CSS files...")
    for css_file in css_files:
        input_path = static_dir / css_file
        output_path = static_dir / css_file.replace('.css', '.min.css')
        
        if input_path.exists():
            if minify_file(input_path, output_path, 'css'):
                success_count += 1
        else:
            print(f"⚠ File not found: {input_path}")
    
    print("\nMinifying JavaScript files...")
    for js_file in js_files:
        input_path = static_dir / js_file
        output_path = static_dir / js_file.replace('.js', '.min.js')
        
        if input_path.exists():
            if minify_file(input_path, output_path, 'js'):
                success_count += 1
        else:
            print(f"⚠ File not found: {input_path}")
    
    print(f"\n✓ Build complete: {success_count}/{total_count} files processed")
    
    if success_count < total_count:
        print("⚠ Some files were not processed. Check warnings above.")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(build_production_assets())

