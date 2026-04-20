#!/usr/bin/env python3
"""
Create sample CSV files to test the CSV preview functionality.
"""

import os
import csv
from pathlib import Path

def create_sample_csv_files():
    """Create sample CSV files for testing."""
    
    test_dir = Path("preview_test_files")
    test_dir.mkdir(exist_ok=True)
    
    print("📋 Creating sample CSV files for testing...")
    
    # Create sample CSV with comma delimiter
    csv_file_comma = test_dir / "sample_data.csv"
    with open(csv_file_comma, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers
        writer.writerow(['ID', 'Name', 'Email', 'Department', 'Salary', 'Start_Date', 'Active'])
        
        # Write sample data
        writer.writerow(['1', 'Alice Johnson', 'alice@company.com', 'Engineering', '75000', '2022-01-15', 'TRUE'])
        writer.writerow(['2', 'Bob Smith', 'bob@company.com', 'Marketing', '65000', '2021-03-20', 'TRUE'])
        writer.writerow(['3', 'Carol Davis', 'carol@company.com', 'Sales', '58000', '2022-06-10', 'TRUE'])
        writer.writerow(['4', 'David Wilson', 'david@company.com', 'Engineering', '82000', '2020-11-05', 'TRUE'])
        writer.writerow(['5', 'Eva Brown', 'eva@company.com', 'HR', '62000', '2023-02-28', 'TRUE'])
        writer.writerow(['6', 'Frank Miller', 'frank@company.com', 'Finance', '78000', '2021-07-12', 'TRUE'])
        writer.writerow(['7', 'Grace Taylor', 'grace@company.com', 'Engineering', '95000', '2012-04-08', 'TRUE'])
        writer.writerow(['8', 'Henry Anderson', 'henry@company.com', 'Marketing', '68000', '2023-01-20', 'FALSE'])
        writer.writerow(['9', 'Ivy Thomas', 'ivy@company.com', 'Sales', '72000', '2022-09-15', 'TRUE'])
        writer.writerow(['10', 'Jack Jackson', 'jack@company.com', 'IT', '85000', '2021-12-01', 'TRUE'])
        writer.writerow(['11', 'Kate White', 'kate@company.com', 'HR', '71000', '2023-03-18', 'TRUE'])
        writer.writerow(['12', 'Liam Harris', 'liam@company.com', 'Finance', '88000', '2020-08-22', 'TRUE'])
        writer.writerow(['13', 'Mia Martin', 'mia@company.com', 'Engineering', '99000', '2011-02-14', 'TRUE'])
        writer.writerow(['14', 'Noah Thompson', 'noah@company.com', 'Marketing', '73000', '2022-11-30', 'FALSE'])
        writer.writerow(['15', 'Olivia Garcia', 'olivia@company.com', 'Sales', '79000', '2021-05-17', 'TRUE'])
    
    print(f"✅ Created CSV file (comma): {csv_file_comma}")
    
    # Create sample CSV with semicolon delimiter
    csv_file_semicolon = test_dir / "sample_data_semicolon.csv"
    with open(csv_file_semicolon, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Write headers
        writer.writerow(['Product_ID', 'Product_Name', 'Category', 'Price', 'Stock', 'Last_Updated'])
        
        # Write sample data
        writer.writerow(['P001', 'Wireless Mouse', 'Electronics', '25.99', '120', '2023-10-15'])
        writer.writerow(['P002', 'USB Keyboard', 'Electronics', '45.50', '85', '2023-10-16'])
        writer.writerow(['P003', 'Laptop Stand', 'Accessories', '35.00', '45', '2023-09-20'])
        writer.writerow(['P004', 'Webcam HD', 'Electronics', '79.99', '30', '2023-10-01'])
        writer.writerow(['P005', 'Desk Lamp', 'Furniture', '55.95', '25', '2023-08-15'])
        writer.writerow(['P006', 'External HDD', 'Electronics', '99.99', '18', '2023-10-10'])
        writer.writerow(['P007', 'Bluetooth Speaker', 'Electronics', '65.00', '40', '2023-09-25'])
        writer.writerow(['P008', 'Phone Charger', 'Electronics', '19.99', '95', '2023-10-12'])
        writer.writerow(['P009', 'Cable Organizer', 'Accessories', '99.50', '60', '2023-07-30'])
        writer.writerow(['P010', 'Monitor Arm', 'Furniture', '149.00', '12', '2023-06-18'])
    
    print(f"✅ Created CSV file (semicolon): {csv_file_semicolon}")
    
    # Create sample CSV with tab delimiter
    csv_file_tab = test_dir / "sample_data_tab.csv"
    with open(csv_file_tab, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        
        # Write headers
        writer.writerow(['Order_ID', 'Customer', 'Product', 'Quantity', 'Total', 'Date'])
        
        # Write sample data
        writer.writerow(['ORD001', 'John Doe', 'Wireless Mouse', '2', '$51.98', '2023-10-01'])
        writer.writerow(['ORD002', 'Jane Smith', 'USB Keyboard', '1', '$45.50', '2023-10-02'])
        writer.writerow(['ORD003', 'Bob Johnson', 'Laptop Stand', '1', '$35.00', '2023-09-20'])
        writer.writerow(['ORD004', 'Alice Brown', 'Webcam HD', '1', '$79.99', '2023-10-01'])
        writer.writerow(['ORD005', 'Charlie Davis', 'Desk Lamp', '2', '$111.90', '2023-08-15'])
        writer.writerow(['ORD006', 'Eva Wilson', 'External HDD', '1', '$99.99', '2023-10-10'])
        writer.writerow(['ORD007', 'Frank Miller', 'Bluetooth Speaker', '3', '$195.00', '2023-09-25'])
        writer.writerow(['ORD008', 'Grace Taylor', 'Phone Charger', '2', '$39.98', '2023-10-12'])
        writer.writerow(['ORD009', 'Henry Anderson', 'Cable Organizer', '4', '$398.00', '2023-07-30'])
        writer.writerow(['ORD010', 'Ivy Thomas', 'Monitor Arm', '1', '$149.00', '2023-06-18'])
    
    print(f"✅ Created CSV file (tab): {csv_file_tab}")
    
    # Create a large CSV file to test performance
    csv_file_large = test_dir / "large_dataset.csv"
    with open(csv_file_large, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers
        writer.writerow(['Row_Number', 'Data_Value', 'Category', 'Timestamp', 'Status'])
        
        # Write 1000 rows of sample data
        for i in range(1, 1001):
            writer.writerow([
                i,
                f'DATA_{i:04d}',
                f'Category_{(i % 10) + 1}',
                f'2023-10-{(i % 28) + 1:02d}',
                'Active' if i % 7 != 0 else 'Inactive'
            ])
    
    print(f"✅ Created large CSV file (1000 rows): {csv_file_large}")
    
    print(f"\n🎉 Sample CSV files created in: {test_dir.absolute()}")
    print("\nCSV files created:")
    print("• sample_data.csv - Standard comma-delimited format")
    print("• sample_data_semicolon.csv - Semicolon-delimited format") 
    print("• sample_data_tab.csv - Tab-delimited format")
    print("• large_dataset.csv - Large file with 1000 rows (performance test)")
    
    print("\nFeatures to test:")
    print("• Automatic delimiter detection")
    print("• Tabular formatting with proper alignment")
    print("• Large file handling (shows first 20 rows)")
    print("• Column limiting (first 15 columns)")
    print("• Cell content truncation for very long values")
    
    return test_dir

if __name__ == "__main__":
    create_sample_csv_files()
