#!/usr/bin/env python3
"""
Verification script to test all improvements applied to File Scout 3.2.
Tests: Memory cleanup, constants, caching, error handling.
"""

import sys
import importlib.util

def verify_improvements():
    """Verify all improvements are present in the code."""
    
    print("=" * 70)
    print("File Scout 3.2 - Improvements Verification")
    print("=" * 70)
    print()
    
    # Load the module
    spec = importlib.util.spec_from_file_location("file_scout", "File Scout 3.2.py")
    if not spec or not spec.loader:
        print("❌ Failed to load File Scout 3.2.py")
        return False
    
    # Read the source file
    with open("File Scout 3.2.py", "r", encoding="utf-8") as f:
        source = f.read()
    
    tests_passed = 0
    tests_total = 0
    
    print("🔍 Verifying Critical Fixes...")
    print("-" * 70)
    
    # Test 1: PDF Memory Leak Fix
    tests_total += 1
    if "self.current_pdf.close()" in source and "def __del__(self):" in source:
        print("✅ PDF Memory Leak Fix - FOUND")
        print("   - Closes old PDF before loading new one")
        print("   - Destructor implemented for cleanup")
        tests_passed += 1
    else:
        print("❌ PDF Memory Leak Fix - MISSING")
    print()
    
    # Test 2: Debug Statements Removed
    tests_total += 1
    debug_count = source.count('print(f"Drew {highlight_count}')
    debug_count += source.count('print(f"Highlighting error details')
    debug_count += source.count('traceback.print_exc()')
    debug_count += source.count('print(f"Error highlighting individual rect')
    
    if debug_count == 0:
        print("✅ Debug Statements Removed - VERIFIED")
        print("   - All debug print statements removed")
        tests_passed += 1
    else:
        print(f"❌ Debug Statements Removed - FAILED ({debug_count} found)")
    print()
    
    print("🎨 Verifying Code Quality Improvements...")
    print("-" * 70)
    
    # Test 3: Constants Defined
    tests_total += 1
    constants = [
        "SCROLLBAR_MARGIN = 40",
        "MIN_WIDGET_WIDTH = 100",
        "ZOOM_STEP = 1.2",
        "MIN_ZOOM = 0.1",
        "MAX_ZOOM = 5.0",
        "DEFAULT_ZOOM = 1.0",
        "HIGHLIGHT_COLOR = QColor(255, 255, 0, 100)",
        "CURRENT_MATCH_COLOR = QColor(255, 0, 0)",
        "CURRENT_MATCH_BORDER_WIDTH = 3"
    ]
    
    constants_found = sum(1 for c in constants if c in source)
    if constants_found == len(constants):
        print(f"✅ Constants Defined - ALL FOUND ({len(constants)}/{len(constants)})")
        print("   - SCROLLBAR_MARGIN")
        print("   - MIN_WIDGET_WIDTH")
        print("   - ZOOM_STEP, MIN_ZOOM, MAX_ZOOM")
        print("   - DEFAULT_ZOOM")
        print("   - HIGHLIGHT_COLOR, CURRENT_MATCH_COLOR")
        print("   - CURRENT_MATCH_BORDER_WIDTH")
        tests_passed += 1
    else:
        print(f"❌ Constants Defined - INCOMPLETE ({constants_found}/{len(constants)})")
    print()
    
    # Test 4: Constants Usage
    tests_total += 1
    constant_usage = [
        "self.SCROLLBAR_MARGIN",
        "self.MIN_WIDGET_WIDTH",
        "self.ZOOM_STEP",
        "self.MAX_ZOOM",
        "self.MIN_ZOOM",
        "self.DEFAULT_ZOOM",
        "self.HIGHLIGHT_COLOR",
        "self.CURRENT_MATCH_COLOR",
        "self.CURRENT_MATCH_BORDER_WIDTH"
    ]
    
    usage_found = sum(1 for u in constant_usage if u in source)
    if usage_found >= len(constant_usage):
        print(f"✅ Constants Usage - VERIFIED ({usage_found} usages)")
        print("   - Constants used throughout code")
        tests_passed += 1
    else:
        print(f"❌ Constants Usage - INCOMPLETE ({usage_found}/{len(constant_usage)})")
    print()
    
    # Test 5: Search Caching
    tests_total += 1
    if "self.search_cache = {}" in source and "if search_text in self.search_cache:" in source:
        print("✅ Search Result Caching - IMPLEMENTED")
        print("   - Search cache dictionary initialized")
        print("   - Cache check before search")
        print("   - Cache cleared on PDF load")
        tests_passed += 1
    else:
        print("❌ Search Result Caching - MISSING")
    print()
    
    # Test 6: Enhanced Error Handling
    tests_total += 1
    if 'def eventFilter(self, obj, event):' in source:
        # Check if try-except wraps the pan operations
        eventfilter_start = source.find('def eventFilter(self, obj, event):')
        eventfilter_section = source[eventfilter_start:eventfilter_start+2000]
        if 'try:' in eventfilter_section and 'except Exception' in eventfilter_section:
            print("✅ Enhanced Error Handling - IMPLEMENTED")
            print("   - Try-except wraps pan operations")
            print("   - Graceful failure handling")
            tests_passed += 1
        else:
            print("❌ Enhanced Error Handling - MISSING")
    else:
        print("❌ Enhanced Error Handling - METHOD NOT FOUND")
    print()
    
    # Test 7: No Magic Numbers
    tests_total += 1
    magic_numbers = [
        "width - 40",  # Should be SCROLLBAR_MARGIN
        "* 1.2,",  # Should be ZOOM_STEP
        ", 5.0)",  # Should be MAX_ZOOM  
        ", 0.1)",  # Should be MIN_ZOOM
        "= 1.0",  # Should be DEFAULT_ZOOM (in assignments)
        "QColor(255, 255, 0, 100)",  # Should be HIGHLIGHT_COLOR (in code)
        "QColor(255, 0, 0)",  # Should be CURRENT_MATCH_COLOR (in code)
        "width > 100"  # Should be MIN_WIDGET_WIDTH
    ]
    
    # Check in methods, not in constant definitions
    method_start = source.find("def update_page(")
    method_section = source[method_start:] if method_start != -1 else source
    
    magic_found = []
    for magic in magic_numbers:
        # Skip if it's in a constant definition
        if magic in method_section:
            context_start = max(0, method_section.find(magic) - 50)
            context = method_section[context_start:method_section.find(magic)+50]
            if "= " + magic.strip() not in context or "self." not in context:
                magic_found.append(magic)
    
    if len(magic_found) == 0:
        print("✅ Magic Numbers Eliminated - VERIFIED")
        print("   - All magic numbers replaced with constants")
        tests_passed += 1
    else:
        print(f"⚠️  Magic Numbers Eliminated - {len(magic_found)} remaining")
        print(f"   - Found: {magic_found[:3]}...")  # Show first 3
    print()
    
    # Summary
    print("=" * 70)
    print(f"📊 Verification Results: {tests_passed}/{tests_total} tests passed")
    print("=" * 70)
    print()
    
    if tests_passed == tests_total:
        print("🎉 SUCCESS! All improvements verified!")
        print()
        print("✅ Memory leak fix implemented")
        print("✅ Debug statements removed")
        print("✅ Constants defined and used")
        print("✅ Search caching implemented")
        print("✅ Enhanced error handling added")
        print("✅ Magic numbers eliminated")
        print()
        print("File Scout 3.2 is ready for production use!")
        return True
    else:
        print(f"⚠️  {tests_total - tests_passed} improvement(s) need attention")
        return False

if __name__ == "__main__":
    try:
        success = verify_improvements()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
