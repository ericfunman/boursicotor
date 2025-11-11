"""
Add necessary imports for constants
"""
import re
from pathlib import Path

BACKEND_DIR = Path("backend")

def add_constants_import(file_path):
    """Add 'from backend.constants import ...' to files using constants"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file uses CONST_ but doesn't import it
    if 'CONST_' in content and 'from backend.constants import' not in content:
        
        # Extract all CONST_ used
        const_names = set(re.findall(r'\bCONST_\w+\b', content))
        
        if const_names:
            import_line = f"from backend.constants import {', '.join(sorted(const_names))}\n"
            
            # Find where to insert (after docstring and other imports)
            lines = content.split('\n')
            insert_pos = 0
            in_docstring = False
            docstring_char = None
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Handle docstrings
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if not in_docstring:
                        in_docstring = True
                        docstring_char = stripped[:3]
                    elif stripped.endswith(docstring_char):
                        in_docstring = False
                    continue
                
                if in_docstring:
                    continue
                
                # Skip blank lines and comments at start
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Found first real line
                if stripped.startswith('import ') or stripped.startswith('from '):
                    # Keep going to find last import
                    insert_pos = i + 1
                else:
                    # No imports yet, insert before this line
                    insert_pos = i
                    break
            
            # Check if import already exists
            lines_str = '\n'.join(lines)
            if 'from backend.constants import' not in lines_str:
                lines.insert(insert_pos, import_line.rstrip())
                
                new_content = '\n'.join(lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return len(const_names)
    
    return 0

def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("📦 ADDING CONSTANTS IMPORTS")
    print("="*60 + "\n")
    
    total_imports = 0
    
    for py_file in sorted(BACKEND_DIR.glob("*.py")):
        if py_file.name == "constants.py":
            continue
        
        count = add_constants_import(py_file)
        if count > 0:
            print(f"  ✅ {py_file.name}: added import ({count} constants)")
            total_imports += count
    
    print(f"\n✅ Import statements added")

if __name__ == "__main__":
    main()
