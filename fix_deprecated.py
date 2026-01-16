#!/usr/bin/env python3
"""
Fix all deprecated use_container_width parameters in Python files
"""
import os
import re

def fix_file(filepath):
    """Fix use_container_width in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace use_container_width=True with nothing (will use default width)
    content = re.sub(r',\s*use_container_width=True', '', content)
    content = re.sub(r'\s*', '', content)
    content = re.sub(r'\(use_container_width=True\)', '()', content)
    
    # Replace use_container_width=False with nothing
    content = re.sub(r',\s*use_container_width=False', '', content)
    content = re.sub(r'\s*', '', content)
    content = re.sub(r'\(use_container_width=False\)', '()', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all Python files in the project"""
    base_dir = '/home/ubuntu/options-trading'
    fixed_count = 0
    
    for root, dirs, files in os.walk(base_dir):
        # Skip backup directories
        if 'backup' in root.lower():
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    print(f"✅ Fixed: {filepath}")
                    fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files!")

if __name__ == '__main__':
    main()
