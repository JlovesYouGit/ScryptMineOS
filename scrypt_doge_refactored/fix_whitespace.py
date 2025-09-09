#!/usr/bin/env python3
"""
Script to fix whitespace issues in Python files.
Removes trailing whitespace and ensures files end with a newline.
"""

import os
import sys

def fix_whitespace(file_path):
    """Fix whitespace issues in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Remove trailing whitespace from each line
    lines = [line.rstrip() + '\n' for line in lines]
    
    # Remove empty lines at the end of the file
    while lines and lines[-1].strip() == '':
        lines.pop()
    
    # Add a single newline at the end of the file
    if lines:
        lines[-1] = lines[-1].rstrip() + '\n'
        lines.append('\n')  # Add final newline
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_whitespace.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if os.path.exists(file_path):
        fix_whitespace(file_path)
        print(f"Fixed whitespace in {file_path}")
    else:
        print(f"File not found: {file_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()