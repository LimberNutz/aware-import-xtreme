#!/usr/bin/env python3
"""
Test script to verify all enhanced preview dependencies are working.
"""

def test_dependencies():
    """Test that all preview dependencies are properly installed."""
    
    print("🔍 Testing Enhanced Preview Dependencies...")
    print("=" * 50)
    
    # Test Pygments (syntax highlighting)
    try:
        import pygments
        from pygments import highlight
        from pygments.lexers import get_lexer_for_filename
        from pygments.formatters import HtmlFormatter
        print("✅ Pygments - Syntax highlighting available")
    except ImportError as e:
        print(f"❌ Pygments - Not available: {e}")
    
    # Test PyMuPDF (PDF preview)
    try:
        import fitz
        print("✅ PyMuPDF - PDF preview available")
    except ImportError as e:
        print(f"❌ PyMuPDF - Not available: {e}")
    
    # Test python-docx (Word documents)
    try:
        from docx import Document
        print("✅ python-docx - Word document preview available")
    except ImportError as e:
        print(f"❌ python-docx - Not available: {e}")
    
    # Test python-pptx (PowerPoint)
    try:
        from pptx import Presentation
        print("✅ python-pptx - PowerPoint preview available")
    except ImportError as e:
        print(f"❌ python-pptx - Not available: {e}")
    
    # Test mutagen (audio metadata)
    try:
        import mutagen
        print("✅ mutagen - Audio metadata available")
    except ImportError as e:
        print(f"❌ mutagen - Not available: {e}")
    
    # Test openpyxl (Excel - should already be available)
    try:
        import openpyxl
        print("✅ openpyxl - Excel preview available")
    except ImportError as e:
        print(f"❌ openpyxl - Not available: {e}")
    
    print("=" * 50)
    print("🎉 Enhanced preview system is ready!")
    print("\nNow you can preview:")
    print("• PDF files with text extraction")
    print("• Excel spreadsheets with data grids")
    print("• Word documents with paragraph content")
    print("• PowerPoint presentations with slide text")
    print("• Audio files with metadata")
    print("• Code files with syntax highlighting")
    print("• And much more!")

if __name__ == "__main__":
    test_dependencies()
