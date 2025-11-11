#!/usr/bin/env python3
"""Find unused exception and loop variables for S1481 fixes."""

import os
import re
from pathlib import Path
from collections import defaultdict

def find_unused_vars(file_path):
    """Find unused exception and loop variables."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    unused = []
    
    # Pattern 1: except Exception as VAR (not used)
    except_pattern = r'except\s+\w+\s+as\s+(\w+):'
    for match in re.finditer(except_pattern, content):
        var_name = match.group(1)
        var_pos = match.end()
        
        # Get content after except clause until next except/for/def/class
        rest_content = content[var_pos:]
        next_structure = re.search(r'\n(except|for|def|class|else:|finally:|\Z)', rest_content)
        if next_structure:
            block_content = rest_content[:next_structure.start()]
        else:
            block_content = rest_content
        
        # Check if variable is used
        if not re.search(rf'\b{re.escape(var_name)}\b', block_content):
            line_num = content[:match.start()].count('\n') + 1
            unused.append(('exception', var_name, line_num, file_path))
    
    return unused

# Scan all backend files
backend_dir = Path('backend')
unused_vars = defaultdict(list)

for py_file in backend_dir.glob('*.py'):
    found = find_unused_vars(py_file)
    if found:
        for var_type, var_name, line_num, file_path in found:
            unused_vars[file_path].append((line_num, var_name))

print("=" * 80)
print("UNUSED VARIABLES (S1481)")
print("=" * 80)

total = 0
for file_path in sorted(unused_vars.keys()):
    print(f"\n📄 {file_path.name}")
    for line_num, var_name in sorted(unused_vars[file_path]):
        print(f"   Line {line_num}: except ... as {var_name}")
        total += 1

print(f"\n{'=' * 80}")
print(f"Total unused exception variables: {total}")
print("=" * 80)
