#!/usr/bin/env python3
"""
Batch process string replacements with safe import handling.
Process files one by one, testing after each.
"""

import subprocess
import sys
from pathlib import Path

# Files to process (sorted by size, smallest first for safety)
FILES_TO_PROCESS = [
    'backend/config.py',
    'backend/celery_config.py',
    'backend/technical_indicators.py',
    'backend/live_data_task.py',
    'backend/tasks.py',
    'backend/job_manager.py',
    'backend/data_interpolator.py',
    'backend/ibkr_connector.py',
    'backend/strategy_adapter.py',
    'backend/strategy_manager.py',
    'backend/yaml_finance_collector.py',
    'backend/models.py',
    'backend/auto_trader.py',
    'backend/data_collector.py',
    'backend/order_manager.py',
    'backend/ibkr_collector.py',
]

# Strings to replace (most common first)
REPLACEMENTS = [
    ('close', 'CONST_CLOSE'),
    ('high', 'CONST_HIGH'),
    ('low', 'CONST_LOW'),
    ('open', 'CONST_OPEN'),
    ('volume', 'CONST_VOLUME'),
    ('timestamp', 'CONST_TIMESTAMP'),
    ('chunk_days', 'CONST_CHUNK_DAYS'),
    ('name', 'CONST_NAME'),
    ('success', 'CONST_SUCCESS'),
]

def process_file_safe(file_path):
    """Process one file with replacements and return results."""
    if not Path(file_path).exists():
        return False, f"File not found: {file_path}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    replacements_made = 0
    constants_needed = set()
    
    # For each replacement string
    for string_value, const_name in REPLACEMENTS:
        # Count occurrences in string literals
        import re
        pattern = rf'(["\']){re.escape(string_value)}\1'
        
        # Find all matches
        matches = list(re.finditer(pattern, content))
        if not matches:
            continue
        
        # Do replacements (right to left to preserve positions)
        for match in reversed(matches):
            # Check context to avoid false positives
            start_line = content.rfind('\n', 0, match.start()) + 1
            end_line = content.find('\n', match.end())
            if end_line == -1:
                end_line = len(content)
            line_context = content[start_line:end_line]
            
            # Skip if in comment
            if '#' in line_context[:match.start() - start_line]:
                continue
            
            # Skip if it's a method/property (to_dict, _name, etc)
            before_context = content[max(0, match.start()-20):match.start()]
            if 'to_' in before_context or '_' + string_value in before_context:
                continue
            
            # Do the replacement
            quote = match.group(1)
            new_value = const_name
            content = content[:match.start()] + new_value + content[match.end():]
            replacements_made += 1
            constants_needed.add(const_name)
    
    # Add import if needed
    if replacements_made > 0:
        # Check if import already exists
        import_exists = f'from backend.constants import' in content
        
        if not import_exists:
            # Find best place to add import (after other imports from backend)
            lines = content.split('\n')
            insert_idx = 0
            in_docstring = False
            docstring_marker = None
            
            for i, line in enumerate(lines):
                # Handle docstrings
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_marker = '"""' if '"""' in line else "'''"
                    elif docstring_marker in line:
                        in_docstring = False
                        insert_idx = i + 1
                        continue
                
                # Skip docstrings
                if in_docstring:
                    continue
                
                # Find backend imports
                if line.startswith('from backend.') or line.startswith('import backend'):
                    insert_idx = i + 1
            
            import_line = f"from backend.constants import {', '.join(sorted(constants_needed))}"
            lines.insert(insert_idx, import_line)
            content = '\n'.join(lines)
    
    # Write back
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Test compilation
        try:
            result = subprocess.run(
                ['python', '-m', 'py_compile', file_path],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                # Restore and return error
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(original)
                return False, f"Compilation failed:\n{result.stderr}"
        except Exception as e:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original)
            return False, f"Test error: {e}"
        
        return True, f"✅ {replacements_made} replacements, {len(constants_needed)} constants"
    
    return True, "No changes needed"

if __name__ == "__main__":
    print("=" * 80)
    print("SAFE BATCH STRING REPLACEMENT")
    print("=" * 80)
    
    total_replacements = 0
    total_files_modified = 0
    
    for file_path in FILES_TO_PROCESS:
        success, message = process_file_safe(file_path)
        status = "✅" if success else "❌"
        print(f"{status} {Path(file_path).name}: {message}")
        
        if success and "replacements" in message:
            count = int(message.split()[1])
            total_replacements += count
            total_files_modified += 1
    
    print(f"\n{'=' * 80}")
    print(f"Total: {total_files_modified} files modified, {total_replacements} replacements")
    print("=" * 80)
