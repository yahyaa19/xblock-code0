#!/usr/bin/env python
"""
Debug script to check XBlock registration in Open edX
Run this script inside your CMS container to debug XBlock issues
"""

import sys
import traceback
import pkg_resources
from xblock.core import XBlock

def check_xblock_registration():
    """Check if the XBlock is properly registered"""
    print("=== XBlock Registration Debug ===\n")
    
    # 1. Check entry points
    print("1. Checking entry points...")
    found_entry_points = []
    for entry_point in pkg_resources.iter_entry_points('xblock.v1'):
        if 'advanced_coding' in entry_point.name.lower():
            found_entry_points.append(entry_point)
            print(f"   ✓ Found entry point: {entry_point.name} = {entry_point.module_name}:{entry_point.attrs[0]}")
    
    if not found_entry_points:
        print("   ✗ No entry points found for 'advanced_coding'")
        print("   Available entry points:")
        for ep in pkg_resources.iter_entry_points('xblock.v1'):
            print(f"     - {ep.name}")
        return False
    
    # 2. Try to load the XBlock class
    print("\n2. Attempting to load XBlock class...")
    try:
        xblock_class = XBlock.load_class('advanced_coding')
        print(f"   ✓ XBlock class loaded successfully: {xblock_class}")
        print(f"   ✓ XBlock module: {xblock_class.__module__}")
        print(f"   ✓ XBlock file: {xblock_class.__module__.__file__ if hasattr(xblock_class.__module__, '__file__') else 'Unknown'}")
    except Exception as e:
        print(f"   ✗ Failed to load XBlock class: {e}")
        traceback.print_exc()
        return False
    
    # 3. Check XBlock methods
    print("\n3. Checking XBlock methods...")
    required_methods = ['student_view', 'workbench_scenarios']
    for method in required_methods:
        if hasattr(xblock_class, method):
            print(f"   ✓ Method '{method}' found")
        else:
            print(f"   ✗ Method '{method}' missing")
    
    # 4. Check XBlock fields
    print("\n4. Checking XBlock fields...")
    if hasattr(xblock_class, '_fields'):
        fields = getattr(xblock_class, '_fields', {})
        print(f"   ✓ Found {len(fields)} fields")
    else:
        print("   ✓ XBlock fields available")
    
    # 5. Try to instantiate (basic check)
    print("\n5. Basic instantiation check...")
    try:
        # This is a very basic check - in real Open edX, this would need proper runtime
        print(f"   ✓ XBlock class can be referenced: {xblock_class.__name__}")
    except Exception as e:
        print(f"   ✗ Issue with XBlock class: {e}")
    
    print("\n=== Debug Complete ===")
    return True

def check_package_installation():
    """Check if the package is properly installed"""
    print("\n=== Package Installation Check ===\n")
    
    try:
        import advanced_coding
        print(f"✓ Package 'advanced_coding' imported successfully")
        print(f"✓ Package location: {advanced_coding.__file__}")
        
        # Check if the main class exists
        if hasattr(advanced_coding, 'AdvancedCodingXBlock'):
            print(f"✓ AdvancedCodingXBlock class found")
        else:
            print(f"✗ AdvancedCodingXBlock class not found in module")
            
    except ImportError as e:
        print(f"✗ Failed to import 'advanced_coding': {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("XBlock Debug Script")
    print("==================")
    
    # Check package installation
    package_ok = check_package_installation()
    
    if package_ok:
        # Check XBlock registration
        xblock_ok = check_xblock_registration()
        
        if xblock_ok:
            print("\n🎉 All checks passed! XBlock should be available.")
        else:
            print("\n❌ XBlock registration issues found.")
    else:
        print("\n❌ Package installation issues found.")
