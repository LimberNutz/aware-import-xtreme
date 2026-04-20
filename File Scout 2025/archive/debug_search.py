#!/usr/bin/env python3
"""
Debug PDF search functionality.
"""

def debug_search_functionality():
    """Debug the PDF search functionality."""
    
    print("🔍 Debugging PDF Search Functionality...")
    print("=" * 50)
    
    try:
        # Read the File Scout code and check search implementation
        with open("File Scout 3.2.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for search method
        if "def search_pdf(self):" in content:
            print("✅ search_pdf method found")
            
            # Extract the method
            start = content.find("def search_pdf(self):")
            end = content.find("\n    def ", start + 1)
            if end == -1:
                end = len(content)
            
            search_method = content[start:end]
            print("📋 search_pdf method content:")
            print(search_method[:500] + "..." if len(search_method) > 500 else search_method)
            
        else:
            print("❌ search_pdf method not found")
        
        # Check for button connections
        if "self.search_btn.clicked.connect(self.search_pdf)" in content:
            print("✅ Search button connected")
        else:
            print("❌ Search button not connected")
        
        if "self.search_input.returnPressed.connect(self.search_pdf)" in content:
            print("✅ Search input Return key connected")
        else:
            print("❌ Search input Return key not connected")
        
        # Check for next search button
        if "def next_search_result(self):" in content:
            print("✅ next_search_result method found")
        else:
            print("❌ next_search_result method not found")
        
        if "self.next_search_btn.clicked.connect(self.next_search_result)" in content:
            print("✅ Next search button connected")
        else:
            print("❌ Next search button not connected")
        
        # Check for potential issues
        print("\n🐛 Checking for potential issues...")
        
        # Look for syntax errors in search method
        if "self.update_page(auto_fit=False, highlight_rects=highlight_rects)" in content:
            print("⚠️  Potential issue: highlight_rects variable might not be defined")
        
        # Check if go_to_search_result method exists
        if "def go_to_search_result(self, index):" in content:
            print("✅ go_to_search_result method found")
        else:
            print("❌ go_to_search_result method missing")
        
        # Check for _get_current_page_highlights method
        if "def _get_current_page_highlights(self):" in content:
            print("✅ _get_current_page_highlights method found")
        else:
            print("❌ _get_current_page_highlights method missing")
        
        print("\n🎯 Analysis:")
        print("The search functionality should work if:")
        print("• search_pdf method exists and is connected")
        print("• go_to_search_result method exists")
        print("• _get_current_page_highlights method exists")
        print("• All buttons are properly connected")
        
    except Exception as e:
        print(f"❌ Error debugging search: {e}")

if __name__ == "__main__":
    debug_search_functionality()
