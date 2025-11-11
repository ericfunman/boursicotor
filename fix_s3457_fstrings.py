#!/usr/bin/env python3
"""
Fix S3457: Empty f-strings (22 issues)
Replace f"text" with "text" when no placeholders are present
"""

import re
from pathlib import Path
import json

def analyze_file_for_empty_fstrings(file_path):
    """Find all empty f-strings in a file"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return []
    
    issues = []
    lines = content.split('\n')
    
    # Pattern: f" or f' followed by text without {} placeholders
    # f"text" or f'text' where no {placeholder} exists
    pattern = r'''f(['"])([^'"]*?)\1(?=\s|,|;|\)|]|$)'''
    
    for line_num, line in enumerate(lines, 1):
        # Look for f-strings without placeholders
        for match in re.finditer(r'f(["\'])([^"\']*?)\1', line):
            inner_string = match.group(2)
            # Check if there are NO curly braces (no placeholders)
            if '{' not in inner_string:
                issues.append({
                    'line': line_num,
                    'text': match.group(0),
                    'inner': inner_string,
                    'col': match.start()
                })
    
    return issues

def fix_empty_fstrings_in_file(file_path):
    """Fix empty f-strings in a file"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return 0
    
    original = content
    
    # Replace all f"text" without placeholders with just "text"
    # This regex finds f followed by quote, captures content, then quote
    # Only replace if no { exists in the string
    
    def replace_fstring(match):
        quote = match.group(1)
        inner = match.group(2)
        # If no curly braces, remove the f
        if '{' not in inner:
            return f'{quote}{inner}{quote}'
        # Otherwise keep as is
        return match.group(0)
    
    # Pattern to match f"..." or f'...'
    content = re.sub(r'f(["\'])([^"\']*?)\1', replace_fstring, content)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return 1
    return 0

def main():
    root = Path(__file__).parent
    backend_dir = root / 'backend'
    frontend_dir = root / 'frontend'
    
    print("=" * 70)
    print("FIXING S3457: Empty f-strings")
    print("=" * 70)
    
    total_fixed = 0
    files_modified = []
    
    # Process backend
    print("\n📁 Processing backend...")
    for py_file in backend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        issues = analyze_file_for_empty_fstrings(py_file)
        if issues:
            fixed = fix_empty_fstrings_in_file(py_file)
            if fixed:
                total_fixed += len(issues)
                files_modified.append(py_file.name)
                print(f"  ✅ {py_file.name}: Fixed {len(issues)} f-strings")
                for issue in issues:
                    print(f"     Line {issue['line']}: {issue['text']}")
    
    # Process frontend
    print("\n📁 Processing frontend...")
    for py_file in frontend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        issues = analyze_file_for_empty_fstrings(py_file)
        if issues:
            fixed = fix_empty_fstrings_in_file(py_file)
            if fixed:
                total_fixed += len(issues)
                files_modified.append(py_file.name)
                print(f"  ✅ {py_file.name}: Fixed {len(issues)} f-strings")
                for issue in issues:
                    print(f"     Line {issue['line']}: {issue['text']}")
    
    print("\n" + "=" * 70)
    print(f"✅ FIXED: {total_fixed} empty f-strings")
    print(f"📝 Files modified: {len(files_modified)}")
    if files_modified:
        print(f"   {', '.join(files_modified)}")
    print("=" * 70)
    
    return total_fixed

if __name__ == '__main__':
    main()
