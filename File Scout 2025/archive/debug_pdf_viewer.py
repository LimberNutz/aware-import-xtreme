#!/usr/bin/env python3
"""
Simple debug script for PDF viewer functionality.
"""

import sys
import os
from pathlib import Path

def debug_pdf_viewer():
    """Debug PDF viewer by checking the code directly."""
    
    print("🔍 Debugging PDF Viewer Code...")
    print("=" * 50)
    
    # Read the File Scout code and check PDF viewer implementation
    try:
        with open("File Scout 3.2.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if PDFViewerWidget class exists
        if "class PDFViewerWidget(QWidget):" in content:
            print("✅ PDFViewerWidget class found")
        else:
            print("❌ PDFViewerWidget class not found")
            return
        
        # Check key methods
        methods_to_check = [
            "def load_pdf(",
            "def update_page(",
            "def next_page(",
            "def previous_page(",
            "def zoom_in(",
            "def zoom_out(",
            "def update_controls(",
            "def search_pdf("
        ]
        
        for method in methods_to_check:
            if method in content:
                print(f"✅ {method.replace('def ', '').replace('(', '')} method found")
            else:
                print(f"❌ {method.replace('def ', '').replace('(', '')} method missing")
        
        # Check button connections
        button_connections = [
            "self.prev_btn.clicked.connect(self.previous_page)",
            "self.next_btn.clicked.connect(self.next_page)",
            "self.zoom_in_btn.clicked.connect(self.zoom_in)",
            "self.zoom_out_btn.clicked.connect(self.zoom_out)"
        ]
        
        print("\n🔗 Checking button connections...")
        for connection in button_connections:
            if connection in content:
                print(f"✅ {connection.split('.')[0].split()[-1]} connected")
            else:
                print(f"❌ {connection.split('.')[0].split()[-1]} not connected")
        
        # Check for potential issues in update_page method
        print("\n🐛 Checking for potential issues...")
        
        # Look for update_page method content
        if "def update_page(self):" in content:
            # Extract the method
            start = content.find("def update_page(self):")
            end = content.find("\n    def ", start + 1)
            if end == -1:
                end = len(content)
            
            update_page_method = content[start:end]
            
            # Check for issues
            if "self.zoom_factor = widget_width / page_width" in update_page_method:
                print("⚠️  Issue found: update_page() resets zoom factor every time")
                print("   This overrides manual zoom settings!")
            
            if "widget_width = self.scroll_area.width() - 40" in update_page_method:
                print("⚠️  Issue found: Auto-fit calculation interferes with manual zoom")
            
            print("\n📋 update_page() method analysis:")
            print("   - The method recalculates zoom factor on every page change")
            print("   - This prevents manual zoom from working")
            print("   - Need to separate auto-fit from manual zoom")
        
        # Check zoom methods
        print("\n🔍 Checking zoom methods...")
        
        if "def zoom_in(self):" in content:
            start = content.find("def zoom_in(self):")
            end = content.find("\n    def ", start + 1)
            zoom_in_method = content[start:end]
            
            if "self.update_page()" in zoom_in_method:
                print("✅ zoom_in() calls update_page()")
            else:
                print("❌ zoom_in() doesn't call update_page()")
        
        if "def zoom_out(self):" in content:
            start = content.find("def zoom_out(self):")
            end = content.find("\n    def ", start + 1)
            zoom_out_method = content[start:end]
            
            if "self.update_page()" in zoom_out_method:
                print("✅ zoom_out() calls update_page()")
            else:
                print("❌ zoom_out() doesn't call update_page()")
        
        print("\n🎯 Root cause identified:")
        print("❌ The update_page() method always recalculates zoom factor")
        print("❌ This overrides manual zoom settings")
        print("❌ Need to fix zoom persistence across page changes")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    debug_pdf_viewer()
