#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix S1192: Duplicated strings - extract to constants
"""
import re
import os
from pathlib import Path
from collections import defaultdict

def find_duplicated_strings():
    """Trouver toutes les strings dupliquées dans le code"""
    
    backend_dir = Path("backend")
    frontend_dir = Path("frontend")
    
    strings_found = defaultdict(list)  # string -> [(file, line_no)]
    
    for py_file in list(backend_dir.glob("*.py")) + list(frontend_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            for line_no, line in enumerate(lines, 1):
                # Trouver les strings littérales (entre quotes)
                # Pattern: "string" ou 'string'
                for match in re.finditer(r'(["\'])(.+?)\1', line):
                    string_val = match.group(2)
                    
                    # Ignorer les strings trop courtes ou spéciales
                    if len(string_val) < 3:
                        continue
                    if string_val.startswith("http"):
                        continue
                    if any(c in string_val for c in ["<", ">", "{", "}"]):
                        continue
                    
                    strings_found[string_val].append((py_file.name, line_no))
        
        except Exception as e:
            print(f"Error in {py_file}: {e}")
    
    # Garder seulement celles dupliquées (2+)
    duplicated = {s: locs for s, locs in strings_found.items() if len(locs) >= 2}
    
    # Trier par fréquence
    sorted_dup = sorted(duplicated.items(), key=lambda x: -len(x[1]))
    
    return sorted_dup[:20]  # Top 20

if __name__ == "__main__":
    duplicated = find_duplicated_strings()
    
    print(f"Found {len(duplicated)} duplicated strings (showing top 20):\n")
    
    for string, locations in duplicated:
        print(f'String: "{string}"')
        print(f"  Occurrences: {len(locations)}")
        for fname, lineno in locations[:3]:
            print(f"    - {fname}:{lineno}")
        if len(locations) > 3:
            print(f"    ... and {len(locations)-3} more")
        print()
