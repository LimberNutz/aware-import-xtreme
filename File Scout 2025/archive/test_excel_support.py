#!/usr/bin/env python3
"""
Test script to verify Excel file support for all formats.
"""

import sys
from pathlib import Path

# Add the current directory to Python path to import File Scout modules
sys.path.insert(0, str(Path(__file__).parent))

def test_excel_handlers():
    """Test all Excel file format handlers."""
    
    print("🔍 Testing Excel File Format Support...")
    print("=" * 50)
    
    # Test imports
    try:
        import openpyxl
        print("✅ openpyxl available - .xlsx/.xlsm support enabled")
    except ImportError:
        print("❌ openpyxl not available")
    
    try:
        import xlrd
        print("✅ xlrd available - .xls support enabled")
    except ImportError:
        print("❌ xlrd not available")
    
    try:
        import xlwt
        print("✅ xlwt available - .xls creation enabled")
    except ImportError:
        print("❌ xlwt not available")
    
    print("=" * 50)
    
    # Import the Excel handler
    try:
        # Import the File Scout modules
        exec(open("File Scout 3.2.py").read())
        
        handler = ExcelPreviewHandler()
        print(f"✅ ExcelPreviewHandler initialized")
        print(f"✅ Supported extensions: {handler.extensions}")
        
        # Test each file format
        test_files = [
            "preview_test_files/sample_data.xls",
            "preview_test_files/sample_data.xlsx", 
            "preview_test_files/sample_macro.xlsm"
        ]
        
        for file_path in test_files:
            if Path(file_path).exists():
                print(f"\n🧪 Testing {file_path}...")
                
                result_type, content, metadata = handler.generate_preview(file_path)
                
                print(f"   Result type: {result_type}")
                print(f"   Content length: {len(content)} characters")
                print(f"   Metadata: {metadata}")
                
                if result_type == "text":
                    lines = content.split('\n')[:3]  # First 3 lines
                    print(f"   Preview:")
                    for line in lines:
                        if line.strip():
                            print(f"      {line[:60]}...")
                elif result_type == "error":
                    print(f"   ❌ Error: {content}")
                else:
                    print(f"   ✅ Success: {result_type}")
            else:
                print(f"❌ File not found: {file_path}")
        
    except Exception as e:
        print(f"❌ Error testing Excel handler: {e}")
    
    print("\n🎉 Excel support test complete!")

if __name__ == "__main__":
    test_excel_handlers()
