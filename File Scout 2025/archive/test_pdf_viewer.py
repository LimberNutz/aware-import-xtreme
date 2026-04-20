#!/usr/bin/env python3
"""
Test script to debug PDF viewer functionality programmatically.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_pdf_viewer_functionality():
    """Test the PDF viewer widget functionality."""
    
    print("🔍 Testing PDF Viewer Functionality...")
    print("=" * 50)
    
    try:
        # Import required modules
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        import fitz
        
        # Create QApplication for testing
        app = QApplication(sys.argv)
        
        # Import the PDF viewer widget
        exec(open("File Scout 3.2.py").read())
        
        # Create PDF viewer instance
        viewer = PDFViewerWidget()
        viewer.show()
        
        print("✅ PDF Viewer widget created successfully")
        
        # Test loading a PDF
        test_pdf = Path("preview_test_files/sample_document.pdf")
        if test_pdf.exists():
            print(f"📄 Loading test PDF: {test_pdf}")
            viewer.load_pdf(str(test_pdf))
            
            # Check if PDF loaded
            if viewer.current_pdf:
                print(f"✅ PDF loaded successfully")
                print(f"   - Pages: {viewer.current_pdf.page_count}")
                print(f"   - Current page: {viewer.current_page}")
                print(f"   - Zoom factor: {viewer.zoom_factor}")
                
                # Test page navigation
                print("\n🧪 Testing page navigation...")
                
                # Test next page
                initial_page = viewer.current_page
                viewer.next_page()
                if viewer.current_page > initial_page:
                    print(f"✅ Next page works: {initial_page} → {viewer.current_page}")
                else:
                    print(f"❌ Next page failed: {initial_page} → {viewer.current_page}")
                
                # Test previous page
                viewer.previous_page()
                if viewer.current_page < initial_page + 1:
                    print(f"✅ Previous page works: {viewer.current_page + 1} → {viewer.current_page}")
                else:
                    print(f"❌ Previous page failed")
                
                # Test zoom functionality
                print("\n🔍 Testing zoom functionality...")
                
                initial_zoom = viewer.zoom_factor
                viewer.zoom_in()
                if viewer.zoom_factor > initial_zoom:
                    print(f"✅ Zoom in works: {initial_zoom:.2f} → {viewer.zoom_factor:.2f}")
                else:
                    print(f"❌ Zoom in failed: {initial_zoom:.2f} → {viewer.zoom_factor:.2f}")
                
                viewer.zoom_out()
                if viewer.zoom_factor < viewer.zoom_factor * 1.2:  # Should be less than after zoom in
                    print(f"✅ Zoom out works: {viewer.zoom_factor:.2f}")
                else:
                    print(f"❌ Zoom out failed: {viewer.zoom_factor:.2f}")
                
                # Test controls state
                print("\n🎮 Testing control states...")
                print(f"   - Previous button enabled: {viewer.prev_btn.isEnabled()}")
                print(f"   - Next button enabled: {viewer.next_btn.isEnabled()}")
                print(f"   - Zoom in button enabled: {viewer.zoom_in_btn.isEnabled()}")
                print(f"   - Zoom out button enabled: {viewer.zoom_out_btn.isEnabled()}")
                print(f"   - Page label: {viewer.page_label.text()}")
                print(f"   - Zoom label: {viewer.zoom_label.text()}")
                
                # Test search functionality
                print("\n🔍 Testing search functionality...")
                viewer.search_input.setText("PDF")
                viewer.search_pdf()
                
                if viewer.search_results:
                    print(f"✅ Search works: Found {len(viewer.search_results)} matches")
                    print(f"   - Next search button enabled: {viewer.next_search_btn.isEnabled()}")
                else:
                    print("❌ Search failed: No results found")
                
                # Test update_page method directly
                print("\n📄 Testing page rendering...")
                try:
                    viewer.update_page()
                    if viewer.pdf_label.pixmap():
                        pixmap = viewer.pdf_label.pixmap()
                        print(f"✅ Page rendering works: {pixmap.width()}x{pixmap.height()} pixels")
                    else:
                        print("❌ Page rendering failed: No pixmap")
                except Exception as e:
                    print(f"❌ Page rendering error: {e}")
                
            else:
                print("❌ Failed to load PDF")
        else:
            print(f"❌ Test PDF not found: {test_pdf}")
        
        print("\n🎯 Testing complete!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_viewer_functionality()
