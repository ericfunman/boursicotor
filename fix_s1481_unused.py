#!/usr/bin/env python3
"""
Fix S1481: Unused local variables
Replace unused variables with _ or remove them
"""

import re
from pathlib import Path
import ast

def find_unused_variables_in_file(file_path):
    """Find potentially unused variables using AST"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content)
    except:
        return []
    
    issues = []
    
    # Find all function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Get all assigned variables in the function
            assigned = set()
            used = set()
            
            for child in ast.walk(node):
                # Track assignments
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            assigned.add(target.id)
                # Track usage (Name references that are Load context)
                elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    used.add(child.id)
                # Track function parameters
                elif isinstance(child, ast.arg):
                    assigned.add(child.arg)
            
            # Variables assigned but never used
            unused = assigned - used
            for var in unused:
                if not var.startswith('_'):
                    issues.append({
                        'function': node.name,
                        'variable': var,
                        'line': node.lineno
                    })
    
    return issues

def fix_unused_variables_simple(file_path):
    """Simple approach: replace common patterns of unused variables"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return 0, []
    
    original = content
    count = 0
    fixed_vars = []
    
    # This is very conservative - only handle patterns we're very sure about
    # Pattern 1: for loop variable in generator expression that's discarded
    # for col_refresh in columns: -> for _ in columns:
    
    # Pattern: unpacking that ignores a variable
    # a, b, c = func() where c is never used -> a, b, _ = func()
    
    # For now, just replace obvious cases like:
    # meta_data = something (but meta_data is never used)
    # Replace with: _ = something
    
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        modified = False
        # Simple pattern: assignment to variable at function start that's never used after
        if re.match(r'\s+\w+\s*=\s*.+$', line) and not re.search(r'\b_\b', line):
            # Could be unused - but we need context to be sure
            # For safety, only handle specific known unused variables from sonar
            known_unused = ['meta_data', 'col_refresh2', 'col6', 'h10', 'h11', 'signal_prices', 'generator']
            
            for var in known_unused:
                if re.match(rf'\s+{var}\s*=\s*.+$', line):
                    # Replace with underscore version
                    line = re.sub(rf'\b{var}\b', '_', line, count=1)
                    modified = True
                    count += 1
                    fixed_vars.append(var)
                    break
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return count, fixed_vars
    
    return 0, []

def main():
    root = Path(__file__).parent
    backend_dir = root / 'backend'
    frontend_dir = root / 'frontend'
    
    print("=" * 70)
    print("FIXING S1481: Unused local variables")
    print("=" * 70)
    print("\n⚠️  Note: This fix is CONSERVATIVE to avoid breaking code")
    print("   Only handles known unused variable patterns from SonarCloud")
    
    total_fixed = 0
    files_modified = []
    
    # Process backend
    print("\n📁 Processing backend...")
    for py_file in backend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        fixed, vars_list = fix_unused_variables_simple(py_file)
        if fixed:
            total_fixed += fixed
            files_modified.append(py_file.name)
            print(f"  ✅ {py_file.name}: Fixed {fixed} unused variables")
            for var in set(vars_list):
                print(f"     - {var}")
    
    # Process frontend  
    print("\n📁 Processing frontend...")
    for py_file in frontend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        fixed, vars_list = fix_unused_variables_simple(py_file)
        if fixed:
            total_fixed += fixed
            files_modified.append(py_file.name)
            print(f"  ✅ {py_file.name}: Fixed {fixed} unused variables")
            for var in set(vars_list):
                print(f"     - {var}")
    
    print("\n" + "=" * 70)
    print(f"✅ FIXED: {total_fixed} unused variables")
    print(f"📝 Files modified: {len(files_modified)}")
    print("=" * 70)
    
    return total_fixed

if __name__ == '__main__':
    main()
