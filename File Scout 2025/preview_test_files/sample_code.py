#!/usr/bin/env python3
"""
Sample Python file for syntax highlighting test.
"""

import os
import sys
from pathlib import Path

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")

if __name__ == "__main__":
    main()
