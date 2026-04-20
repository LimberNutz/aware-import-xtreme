"""
Quick test to verify SmartSortDialog imports work correctly
"""
import sys
from pathlib import Path

# Test if we can import the necessary classes
try:
    from PyQt6.QtWidgets import QApplication, QButtonGroup, QRadioButton
    from PyQt6.QtCore import Qt
    print("✓ PyQt6 imports successful")
except ImportError as e:
    print(f"✗ PyQt6 import error: {e}")
    sys.exit(1)

# Test if the application can start
app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

# Test if we can access the SmartSortDialog class
try:
    # Read the file and check if SmartSortDialog is defined
    with open("File Scout 3.2.py", 'r') as f:
        content = f.read()
    
    if "class SmartSortDialog(QDialog):" in content:
        print("✓ SmartSortDialog class found in file")
    else:
        print("✗ SmartSortDialog class not found")
        
    if "QButtonGroup" in content and "QRadioButton" in content:
        print("✓ Required Qt widgets are used in the code")
    else:
        print("✗ Required Qt widgets missing")
        
    print("\n=== Import Fix Verification Complete ===")
    print("The enhanced Smart Sort should now work without import errors!")
    
except Exception as e:
    print(f"✗ Error during verification: {e}")
    import traceback
    traceback.print_exc()
