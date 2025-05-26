#!/usr/bin/env python3
"""
Fix script to ensure enhanced_order_dialog.py is properly updated.
This removes any cached modules and ensures the correct code is in place.
"""

import os
import sys
import importlib

def fix_enhanced_dialog():
    """Fix the enhanced order dialog by clearing cache and reloading."""
    print("Fixing enhanced order dialog...")
    
    # Remove any cached Python files
    cache_files = [
        "__pycache__/enhanced_order_dialog.cpython-*.pyc",
        "enhanced_order_dialog.pyc"
    ]
    
    for pattern in cache_files:
        import glob
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"Removed cache file: {file}")
            except:
                pass
    
    # If module is loaded, remove it from cache
    if 'enhanced_order_dialog' in sys.modules:
        del sys.modules['enhanced_order_dialog']
        print("Removed module from Python cache")
    
    # Try to import and check if it has the correct method
    try:
        import enhanced_order_dialog
        # Check if create_labeled_frame exists
        if hasattr(enhanced_order_dialog.EnhancedOrderDialog, 'create_labeled_frame'):
            print("✓ Enhanced dialog has the correct create_labeled_frame method")
        else:
            print("✗ Enhanced dialog is missing create_labeled_frame method")
            print("  The file may need to be manually updated or re-downloaded")
    except Exception as e:
        print(f"Error checking module: {e}")
    
    print("\nPlease restart your application for changes to take effect.")
    print("If the error persists, try:")
    print("1. Close all Python processes")
    print("2. Delete __pycache__ directory")
    print("3. Restart your Python environment")

if __name__ == "__main__":
    fix_enhanced_dialog()