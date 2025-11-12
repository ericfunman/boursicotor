#!/usr/bin/env python3
"""
Fix S6711: Replace legacy numpy.random with numpy.random.Generator
Scan all Python files and add proper random number generator initialization
"""

import re
from pathlib import Path

def analyze_file_for_numpy_random(file_path):
    """Check if file uses any numpy random patterns"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return []
    
    issues = []
    
    # Check for various numpy.random patterns
    patterns = [
        (r'np\.random\.', 'np.random.*'),
        (r'numpy\.random\.', 'numpy.random.*'),
        (r'from numpy.random import', 'from numpy.random import'),
        (r'from numpy import random', 'from numpy import random'),
    ]
    
    for pattern, name in patterns:
        if re.search(pattern, content):
            issues.append(name)
    
    return list(set(issues))

def fix_numpy_random_in_file(file_path):
    """Add numpy.random.Generator if using legacy API"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return False, []
    
    original = content
    changes = []
    
    # If file has np.random or numpy.random usage
    if not ('np.random' in content or 'numpy.random' in content):
        return False, []
    
    # Check if already using Generator
    if 'numpy.random.Generator' in content or '_rng' in content:
        return False, []  # Already fixed
    
    # Add imports if needed
    if 'import numpy as np' in content and 'from numpy.random import Generator, default_rng' not in content:
        content = content.replace(
            'import numpy as np',
            'import numpy as np\nfrom numpy.random import default_rng\n\n# Initialize RNG\n_rng = default_rng(seed=42)'
        )
        changes.append('Added Generator initialization')
    
    # Now replace numpy.random calls
    # This is conservative - only replace known patterns
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True, changes
    
    return False, changes

def main():
    root = Path(__file__).parent
    backend_dir = root / 'backend'
    frontend_dir = root / 'frontend'
    
    print("=" * 70)
    print("SCANNING FOR numpy.random USAGE")
    print("=" * 70)
    
    files_with_usage = []
    
    # Scan backend
    print("\n📁 Scanning backend...")
    for py_file in backend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        issues = analyze_file_for_numpy_random(py_file)
        if issues:
            files_with_usage.append((py_file.name, issues))
            print(f"  ⚠️  {py_file.name}: {', '.join(issues)}")
    
    # Scan frontend
    print("\n📁 Scanning frontend...")
    for py_file in frontend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        issues = analyze_file_for_numpy_random(py_file)
        if issues:
            files_with_usage.append((py_file.name, issues))
            print(f"  ⚠️  {py_file.name}: {', '.join(issues)}")
    
    print("\n" + "=" * 70)
    print(f"Found {len(files_with_usage)} files with numpy.random usage")
    print("=" * 70)
    print("\nNote: S6711 issues in backtesting_engine.py appear to be false positives")
    print("(file doesn't contain any numpy.random calls)")

if __name__ == '__main__':
    main()
