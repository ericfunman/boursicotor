#!/usr/bin/env python3
"""
Fix Sonar issues that are NOT related to method complexity
- S117: Naming conventions (parameter names)
- S3457: F-strings with no replacement fields
- S1481: Unused loop index
- S5754: Exception handling (catch/reraise)
- S5914: Identity assertions
"""
import re
import json

def fix_s3457_fstrings():
    """Fix F-strings with no replacement fields (empty f-strings)"""
    print("\n" + "="*80)
    print("[S3457] Fixing empty f-strings")
    print("="*80)
    
    files_to_fix = {
        "backend/ibkr_collector.py": [1588, 1625],
        "backend/live_price_thread.py": [79, 90, 138],
    }
    
    for filepath, lines in files_to_fix.items():
        print(f"\nProcessing {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # Find and fix f-strings with no {} placeholders
            for line_num in lines:
                lines_list = content.split('\n')
                if line_num - 1 < len(lines_list):
                    line = lines_list[line_num - 1]
                    print(f"  Line {line_num}: {line.strip()[:80]}")
                    
                    # Replace f"text" with "text" when no {} present
                    if 'f"' in line and '{' not in line:
                        content = content.replace(f'f"{line[line.find("f") + 2:line.rfind('"')]}', 
                                               f'"{line[line.find("f") + 2:line.rfind('"')]}', 1)
                    elif "f'" in line and '{' not in line:
                        content = content.replace(f"f'{line[line.find("f") + 2:line.rfind("'")]}",
                                               f"'{line[line.find("f") + 2:line.rfind("'")]}', 1)
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed {len(lines)} f-string issues")
            else:
                print(f"  ⚠️ Could not fix automatically - manual review needed")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def fix_s1481_unused_index():
    """Fix unused loop index - replace 'i' with '_'"""
    print("\n" + "="*80)
    print("[S1481] Fixing unused loop index")
    print("="*80)
    
    filepath = "backend/data_collector.py"
    line_num = 532
    
    print(f"\nProcessing {filepath}:{line_num}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if line_num - 1 < len(lines):
            line = lines[line_num - 1]
            print(f"  Original: {line.strip()[:80]}")
            
            # Replace "for i in" with "for _ in" where i is not used
            if "for i in" in line:
                lines[line_num - 1] = line.replace("for i in", "for _ in")
                print(f"  Fixed: {lines[line_num - 1].strip()[:80]}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"  ✅ Fixed unused index")
            else:
                print(f"  ⚠️ Pattern not found, manual review needed")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def fix_s5754_exception_handling():
    """Fix exception handling - specify exception class"""
    print("\n" + "="*80)
    print("[S5754] Fixing exception handling")
    print("="*80)
    
    filepath = "backend/live_price_thread.py"
    line_num = 139
    
    print(f"\nProcessing {filepath}:{line_num}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        if line_num - 1 < len(lines):
            line = lines[line_num - 1]
            print(f"  Original: {line.strip()[:80]}")
            
            # Find context - should be a bare except
            if 'except:' in line:
                print(f"  Found bare except statement")
                # Context: usually after a try block for disconnection
                context_start = max(0, line_num - 5)
                for i in range(context_start, min(line_num + 2, len(lines))):
                    print(f"    {i+1}: {lines[i][:80]}")
                
                # Replace bare except with Exception
                lines[line_num - 1] = line.replace('except:', 'except Exception:')
                print(f"  Fixed: {lines[line_num - 1].strip()[:80]}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                print(f"  ✅ Fixed exception handling")
            else:
                print(f"  ⚠️ Not a bare except, manual review needed")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def fix_s5914_identity_assertion():
    """Fix identity assertion - remove constant assertions"""
    print("\n" + "="*80)
    print("[S5914] Fixing identity assertion")
    print("="*80)
    
    filepath = "tests/test_order_manager_focused.py"
    line_num = 33
    
    print(f"\nProcessing {filepath}:{line_num}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if line_num - 1 < len(lines):
            line = lines[line_num - 1]
            print(f"  Original: {line.strip()[:80]}")
            
            # Show context
            context_start = max(0, line_num - 3)
            for i in range(context_start, min(line_num + 2, len(lines))):
                print(f"    {i+1}: {lines[i].strip()[:80]}")
            
            # This is an identity check with constant value - should probably be removed or changed
            if 'is' in line and ('True' in line or 'False' in line or 'None' in line):
                print(f"  ℹ️ This is likely an identity check with a constant")
                print(f"  Action: Remove or change to equality check (==)")
                print(f"  Manual review required")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def fix_s117_naming_conventions():
    """Fix S117 - Parameter naming conventions (camelCase to snake_case)"""
    print("\n" + "="*80)
    print("[S117] Fixing parameter naming conventions")
    print("="*80)
    print("\nNote: S117 issues are in ibkr_connector.py parameter names")
    print("These are callback function parameters from IBKR API")
    print("Recommended: Use # noqa comments or suppress via SonarCloud config")
    print("\nIssues found:")
    print("  - advancedOrderRejectJson → advanced_order_reject_json")
    print("  - errorCode → error_code")
    print("  - errorString → error_string")
    print("  - reqId → req_id")
    print("  - orderId → order_id")
    print("\n⚠️ Note: These are IBKR API callback signatures - cannot be changed")
    print("Action: Add @SuppressWarnings or use noqa comment")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("FIX SONAR ISSUES (Non-Complexity)")
    print("="*80)
    
    print("\n📊 Summary of issues to fix:")
    print("  S3457: 5 issues - Empty f-strings")
    print("  S1481: 1 issue  - Unused loop index")
    print("  S5754: 1 issue  - Exception handling")
    print("  S5914: 1 issue  - Identity assertion")
    print("  S117:  14 issues - Parameter naming (IBKR API - cannot fix)")
    
    # Fix issues in order
    fix_s3457_fstrings()
    fix_s1481_unused_index()
    fix_s5754_exception_handling()
    fix_s5914_identity_assertion()
    fix_s117_naming_conventions()
    
    print("\n" + "="*80)
    print("✅ DONE - Check diffs before committing")
    print("="*80)
