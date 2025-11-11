#!/usr/bin/env python3
"""Safe string replacement with proper import handling."""

import os
import re
from pathlib import Path
from collections import defaultdict

# Mapping de strings à remplacer
STRING_REPLACEMENTS = {
    "timestamp": "CONST_TIMESTAMP",
    "chunk_days": "CONST_CHUNK_DAYS",
    "high": "CONST_HIGH",
    "low": "CONST_LOW",
    "open": "CONST_OPEN",
    "close": "CONST_CLOSE",
    "volume": "CONST_VOLUME",
    "name": "CONST_NAME",
    "success": "CONST_SUCCESS",
    "exchange": "CONST_EXCHANGE",
    "currency": "CONST_CURRENCY",
    "isin": "CONST_ISIN",
    "1min": "CONST_1MIN",
    "5min": "CONST_5MIN",
    "15min": "CONST_15MIN",
    "30min": "CONST_30MIN",
    "1h": "CONST_1HOUR",
    "1d": "CONST_1DAY",
    "1w": "CONST_1WEEK",
    "1M": "CONST_1MONTH",
}

def safe_replace_strings_in_file(file_path):
    """Replace strings while ensuring imports are added."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    replacements_made = []
    constants_needed = set()
    
    # Find all string literals in the file (simple approach)
    for string_value, const_name in STRING_REPLACEMENTS.items():
        # Match quoted strings: "string" or 'string'
        pattern = rf'(["\'])({re.escape(string_value)})\1'
        
        # Skip if it's a dictionary key pattern or method name
        matches = list(re.finditer(pattern, content))
        for match in matches:
            # Check context - avoid replacing in special cases
            start = max(0, match.start() - 50)
            context_before = content[start:match.start()]
            context_after = content[match.end():min(len(content), match.end() + 50)]
            
            # Skip if it's a method name like .to_dict()
            if 'to_' in context_before or '_dict' in context_after:
                continue
            
            # Skip if it's in a docstring or comment
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_before_comment = content[line_start:match.start()]
            if '#' in line_before_comment or '"""' in line_before_comment or "'''" in line_before_comment:
                continue
            
            constants_needed.add(const_name)
            replacements_made.append((string_value, const_name, match.start()))
    
    # Now do the replacements
    offset = 0
    for string_value, const_name, pos in replacements_made:
        pattern = rf'(["\'])({re.escape(string_value)})\1'
        matches = list(re.finditer(pattern, content))
        
        for match in matches:
            if match.group(2) == string_value:
                # Replace "value" with CONST_NAME
                content = content[:match.start()] + const_name + content[match.end():]
                break
    
    # Add import at the top if needed
    if constants_needed and content != original_content:
        # Find the right place to add import
        import_line = f"from backend.constants import {', '.join(sorted(constants_needed))}\n"
        
        # Find where to insert (after existing imports from backend)
        lines = content.split('\n')
        insert_idx = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from backend.'):
                insert_idx = i + 1
            elif line.startswith('import ') and i > insert_idx:
                break
            elif line.startswith('"""') or line.startswith("'''"):
                # After docstring
                for j in range(i + 1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        insert_idx = j + 1
                        break
        
        # Check if import already exists
        existing_import = any(import_line.strip() in line for line in lines if 'from backend.constants' in line)
        
        if not existing_import and constants_needed:
            lines.insert(insert_idx, import_line.rstrip())
            content = '\n'.join(lines)
    
    # Write back only if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return len(replacements_made), len(constants_needed)
    
    return 0, 0

# Process all backend files
backend_dir = Path('backend')
total_replacements = 0
total_files_modified = 0

print("=" * 80)
print("SAFE STRING REPLACEMENT WITH IMPORTS")
print("=" * 80)

for py_file in sorted(backend_dir.glob('*.py')):
    if py_file.name == 'constants.py':
        continue
    
    reps, consts = safe_replace_strings_in_file(py_file)
    if reps > 0:
        print(f"✅ {py_file.name}: {reps} replacements, {consts} constants imported")
        total_replacements += reps
        total_files_modified += 1

print(f"\n{'=' * 80}")
print(f"Total replacements: {total_replacements}")
print(f"Total files modified: {total_files_modified}")
print("=" * 80)
