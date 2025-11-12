#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix S7498: Replace dict() calls with {} literals
"""
import re
from pathlib import Path

def fix_dict_literals():
    """Remplacer dict() par {} dans tout le code"""
    
    backend_files = list(Path("backend").glob("*.py"))
    frontend_files = list(Path("frontend").glob("*.py"))
    all_files = backend_files + frontend_files
    
    total_fixed = 0
    
    for py_file in all_files:
        if py_file.name.startswith("_"):
            continue
        
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            
            # Pattern: dict() sans arguments -> {}
            # Mais attention aux dict(key=value)
            # On remplace seulement dict() vide ou avec des args simples
            
            # dict() -> {}
            content = re.sub(r'\bdict\(\s*\)', '{}', content)
            
            if content != original:
                count = len(re.findall(r'\bdict\(\s*\)', original))
                with open(py_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[{py_file.name}] Fixed {count} dict() calls")
                total_fixed += count
        
        except Exception as e:
            print(f"Error in {py_file}: {e}")
    
    print(f"\nTotal dict() -> {{}} replacements: {total_fixed}")
    return total_fixed

if __name__ == "__main__":
    fix_dict_literals()
