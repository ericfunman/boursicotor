"""
Intelligent string replacement in codebase
Replaces duplicated string literals with references to constants
"""
import re
from pathlib import Path

BACKEND_DIR = Path("backend")

# Map of string values to constant names
REPLACEMENTS = {
    '"timestamp"': 'CONST_TIMESTAMP',
    "'timestamp'": 'CONST_TIMESTAMP',
    '"high"': 'CONST_HIGH',
    "'high'": 'CONST_HIGH',
    '"low"': 'CONST_LOW',
    "'low'": 'CONST_LOW',
    '"open"': 'CONST_OPEN',
    "'open'": 'CONST_OPEN',
    '"close"': 'CONST_CLOSE',
    "'close'": 'CONST_CLOSE',
    '"volume"': 'CONST_VOLUME',
    "'volume'": 'CONST_VOLUME',
}

def replace_strings_in_file(file_path):
    """Replace duplicated strings in a Python file"""
    
    if file_path.name == "constants.py":
        return 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    replacements_made = 0
    
    # Only replace in specific contexts (DataFrame operations, dict keys, etc)
    for string_literal, const_name in REPLACEMENTS.items():
        # Pattern: df["column"] -> df[CONST_COLUMN]
        # Pattern: dict keys, assignments, etc
        
        patterns = [
            # df["column"] or df['column']
            (rf'(\[){string_literal}(\])', rf'\1{const_name}\2'),
            # "column" = value or 'column' = value
            (rf'(\[){string_literal}(\s*=)', rf'\1{const_name}\2'),
            # in dictionary: "column": value
            (rf'({string_literal}\s*:)', rf'{const_name}:'),
        ]
        
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            count = len(re.findall(pattern, content))
            if count > 0:
                replacements_made += count
                content = new_content
    
    if content != original:
        # Add import if needed
        if 'CONST_' in content and 'from backend.constants import' not in content:
            # Add import at the beginning after docstring and other imports
            lines = content.split('\n')
            
            import_inserted = False
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    # Find the last import
                    continue
                elif line and not line.startswith('"""') and not line.startswith("'''") and not line.startswith('#'):
                    if not import_inserted:
                        # Insert before first non-import, non-comment line
                        lines.insert(i, 'from backend.constants import CONST_TIMESTAMP, CONST_HIGH, CONST_LOW, CONST_OPEN, CONST_CLOSE, CONST_VOLUME')
                        import_inserted = True
                    break
            
            content = '\n'.join(lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return replacements_made

def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("🔄 REPLACING DUPLICATED STRINGS WITH CONSTANTS")
    print("="*60 + "\n")
    
    total_replacements = 0
    
    for py_file in sorted(BACKEND_DIR.glob("*.py")):
        if py_file.name.startswith("test_"):
            continue
        
        count = replace_strings_in_file(py_file)
        if count > 0:
            print(f"  ✅ {py_file.name}: {count} replacements")
            total_replacements += count
    
    print(f"\n✅ Total replacements: {total_replacements}")
    print("\nNote: Manual review recommended for complex refactorings")

if __name__ == "__main__":
    main()
