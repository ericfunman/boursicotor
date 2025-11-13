#!/usr/bin/env python3
import sys
try:
    with open('frontend/app.py', 'rb') as f:
        content = f.read()
    compile(content, 'frontend/app.py', 'exec')
    print('✅ Syntaxe OK')
except SyntaxError as e:
    print(f'❌ SyntaxError at line {e.lineno}: {e.msg}')
    if e.text:
        print(f'  {e.text}')
    sys.exit(1)
