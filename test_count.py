#!/usr/bin/env python3
"""Test des fixes"""
from pathlib import Path
import re

backend = Path('backend')
count = 0

for f in backend.rglob('*.py'):
    try:
        content = f.read_text(encoding='utf-8', errors='ignore')
        stripped = content.lstrip()
        
        # Skip if already has doc
        if stripped.startswith(('"""', "'''", '#')):
            continue
        
        if len(content.strip()) < 50:
            continue
        
        count += 1
        print(f"  Need docstring: {f.name}")
        
    except:
        pass

print(f'Total: {count} fichiers')
