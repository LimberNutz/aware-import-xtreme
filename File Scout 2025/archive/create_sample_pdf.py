#!/usr/bin/env python3
"""
Create a sample PDF file to test the enhanced PDF preview system.
"""

import os
from pathlib import Path

def create_sample_pdf():
    """Create a sample PDF document for testing."""
    
    test_dir = Path("preview_test_files")
    test_dir.mkdir(exist_ok=True)
    
    print("📋 Creating sample PDF for enhanced preview...")
    
    try:
        import fitz  # PyMuPDF
        
        # Create a new PDF document
        doc = fitz.open()  # Create empty PDF
        
        # Page 1 - Title and Introduction
        page = doc.new_page()
        text = "FILE SCOUT 3.2\nEnhanced Preview System\n"
        text += "=" * 50 + "\n\n"
        text += "This is a sample PDF document created to demonstrate the enhanced PDF preview capabilities in File Scout 3.2.\n\n"
        text += "The preview system now features:\n"
        text += "• Text extraction from PDF documents\n"
        text += "• Dual-tab preview system\n"
        text += "• Formatted document display with page numbers\n"
        text += "• Support for multi-page documents\n"
        text += "• Enhanced metadata extraction\n\n"
        text += "This demonstrates how File Scout can display PDF content directly in the preview pane without requiring external PDF readers."
        
        page.insert_text((50, 50), text, fontsize=12, fontname="helvetica")
        
        # Page 2 - Technical Details
        page = doc.new_page()
        text = "TECHNICAL IMPLEMENTATION\n"
        text += "=" * 50 + "\n\n"
        text += "PDF Preview Architecture:\n\n"
        text += "1. PyMuPDF Integration\n"
        text += "   - Text extraction from PDF pages\n"
        text += "   - Page boundary detection\n"
        text += "   - Metadata parsing\n\n"
        text += "2. Dual-Tab Display System\n"
        text += "   - Text tab: Simple content view\n"
        text += "   - PDF Document tab: Formatted with page numbers\n"
        text += "   - Properties tab: File metadata\n\n"
        text += "3. Performance Optimizations\n"
        text += "   - Limited to first 3 pages for preview\n"
        text += "   - Memory-efficient text extraction\n"
        text += "   - Graceful error handling\n\n"
        text += "This system provides users with immediate PDF content inspection capabilities."
        
        page.insert_text((50, 50), text, fontsize=11, fontname="helvetica")
        
        # Page 3 - Features and Benefits
        page = doc.new_page()
        text = "FEATURES AND BENEFITS\n"
        text += "=" * 50 + "\n\n"
        text += "Enhanced PDF Preview Provides:\n\n"
        text += "✓ Instant Content Preview\n"
        text += "   - No external applications required\n"
        text += "   - Fast text extraction and display\n"
        text += "   - Multi-page document support\n\n"
        text += "✓ Professional Document Display\n"
        text += "   - Formatted text with proper spacing\n"
        text += "   - Page number indicators\n"
        text += "   - Clean, readable formatting\n\n"
        text += "✓ Integration with File Scout\n"
        text += "   - Seamless tab-based interface\n"
        text += "   - Consistent with other preview types\n"
        text += "   - Enhanced file management workflow\n\n"
        text += "This transforms File Scout into a comprehensive document inspection tool."
        
        page.insert_text((50, 50), text, fontsize=11, fontname="helvetica")
        
        # Save the PDF
        pdf_file = test_dir / "sample_document.pdf"
        doc.save(pdf_file)
        doc.close()
        
        print(f"✅ Created PDF file: {pdf_file}")
        print(f"📄 PDF contains 3 pages with sample content")
        
        return pdf_file
        
    except ImportError:
        print("❌ PyMuPDF not available - cannot create sample PDF")
        return None
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return None

if __name__ == "__main__":
    create_sample_pdf()
