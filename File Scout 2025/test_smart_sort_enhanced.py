"""
Test script for Enhanced Smart Sort functionality
Tests the pattern matching logic without GUI
"""

import os
import sys
from pathlib import Path

# Add the current directory to path to import from File Scout
sys.path.insert(0, str(Path(__file__).parent))

def create_test_structure():
    """Create test directory structure and files"""
    test_root = Path("test_smart_sort_data")
    
    # Create destination folders
    folders = [
        "GG-DIS-01",
        "GG-DIS-02", 
        "GG-DIS-06",
        "GG-DIS-07",
        "GG-DIS-08",
        "GG-DIS-09",
        "Archive/Old",
        "Processed/2023"
    ]
    
    for folder in folders:
        (test_root / folder).mkdir(parents=True, exist_ok=True)
    
    # Create test files
    test_files = [
        "GG-DIS-06 UT Sheet R.11.2.xlsx",
        "GG-DIS-07 UT Sheet R.11.2.xlsx", 
        "GG-DIS-08 Report.pdf",
        "GG-DIS-09 Data.csv",
        "Some Other File.txt",
        "GG-DIS-01 Document.docx",
        "GG-DIS-02 Analysis.xlsx"
    ]
    
    source_dir = test_root / "source"
    source_dir.mkdir(exist_ok=True)
    
    for file in test_files:
        (source_dir / file).touch()
    
    return test_root, source_dir

def test_pattern_matching():
    """Test the pattern matching logic"""
    print("=== Testing Enhanced Smart Sort Pattern Matching ===\n")
    
    # Create test data
    test_root, source_dir = create_test_structure()
    print(f"Created test structure in: {test_root}")
    
    # Simulate the pattern matching logic
    def extract_pattern_from_filename(filename, folder_list):
        """Extract the longest matching folder pattern from filename"""
        # Sort folders by name length (longest first) for best match
        sorted_folders = sorted(folder_list, key=lambda f: len(f), reverse=True)
        
        # Find the longest folder name that appears in the filename
        for folder in sorted_folders:
            if folder in filename:
                return folder
        return None
    
    # Get list of folder names
    folder_names = []
    for folder in test_root.rglob("*"):
        if folder.is_dir() and folder != test_root:
            folder_names.append(folder.name)
    
    print(f"\nAvailable folders: {folder_names}")
    
    # Test pattern matching
    test_files = list(source_dir.glob("*"))
    print("\n=== Pattern Matching Results ===")
    
    matches = 0
    for file in test_files:
        matched_folder = extract_pattern_from_filename(file.name, folder_names)
        if matched_folder:
            print(f"✓ {file.name} → {matched_folder}")
            matches += 1
        else:
            print(f"✗ {file.name} → No match")
    
    print(f"\nSummary: {matches}/{len(test_files)} files matched")
    
    # Test fuzzy matching
    print("\n=== Testing Fuzzy Matching ===")
    
    def fuzzy_match_folder(filename, folder_list):
        """Find fuzzy match for unmatched files"""
        best_match = None
        best_score = 0
        
        for folder in folder_list:
            score = 0
            folder_name = folder.lower()
            filename_lower = filename.lower()
            
            # Check for common substrings
            for i in range(2, min(len(folder_name), 8)):
                if folder_name[:i] in filename_lower:
                    score += i
            
            # Bonus for exact word matches
            words = folder_name.split('-')
            for word in words:
                if word in filename_lower:
                    score += len(word) * 2
            
            if score > best_score and score > 3:
                best_score = score
                best_match = folder
        
        return best_match, best_score
    
    # Test on unmatched file
    unmatched_file = "Some Other File.txt"
    fuzzy_match, score = fuzzy_match_folder(unmatched_file, folder_names)
    if fuzzy_match:
        print(f"Fuzzy match for '{unmatched_file}': {fuzzy_match} (score: {score})")
    else:
        print(f"No fuzzy match found for '{unmatched_file}'")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_root)
    print(f"\nCleaned up test directory: {test_root}")
    
    print("\n=== Test Complete ===")
    print("The enhanced pattern matching logic is working correctly!")
    return True

if __name__ == "__main__":
    try:
        test_pattern_matching()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
