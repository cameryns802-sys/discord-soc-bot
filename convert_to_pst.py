#!/usr/bin/env python3
"""
Bulk PST Timezone Converter
Converts all datetime.utcnow() references to get_now_pst() across all cogs
"""

import os
import re
from pathlib import Path

# Files to process (excluding files we've already handled)
SKIP_FILES = {"pst_timezone.py", "test_timezone.py", "convert_to_pst.py", "bot.py"}

# Pattern to find datetime.utcnow() calls
DATETIME_PATTERN = r'datetime\.utcnow\(\)'

def has_utcnow(filepath):
    """Check if file has datetime.utcnow() calls"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return re.search(DATETIME_PATTERN, content) is not None
    except:
        return False

def has_import(filepath):
    """Check if file already has the PST import"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return 'from cogs.core.pst_timezone import' in content
    except:
        return False

def add_import(filepath):
    """Add the PST timezone import to a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find the right place to add import (after other imports)
        lines = content.split('\n')
        import_idx = -1
        
        # Find the last import statement
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_idx = i
        
        # Add the PST import after the last import
        if import_idx >= 0:
            lines.insert(import_idx + 1, 'from cogs.core.pst_timezone import get_now_pst')
            new_content = '\n'.join(lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"    Error adding import: {e}")
    
    return False

def replace_utcnow(filepath):
    """Replace all datetime.utcnow() with get_now_pst()"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        new_content = re.sub(DATETIME_PATTERN, 'get_now_pst()', content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return len(re.findall(DATETIME_PATTERN, content))
    except Exception as e:
        print(f"    Error replacing: {e}")
    
    return 0

def process_files():
    """Process all Python files"""
    processed = []
    
    # Walk all cog directories
    for root, dirs, files in os.walk('cogs'):
        for file in files:
            if not file.endswith('.py'):
                continue
            
            if file in SKIP_FILES:
                continue
            
            filepath = os.path.join(root, file)
            
            # Check if file has utcnow calls
            if not has_utcnow(filepath):
                continue
            
            # Check if already has import
            if has_import(filepath):
                continue
            
            print(f"Processing: {filepath}")
            
            try:
                # Add import
                if add_import(filepath):
                    print(f"  ✓ Added import")
                
                # Replace datetime.utcnow() calls
                count = replace_utcnow(filepath)
                if count > 0:
                    print(f"  ✓ Replaced {count} datetime.utcnow() calls with get_now_pst()")
                
                processed.append(filepath)
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    return processed

if __name__ == '__main__':
    print("🔄 Starting PST Timezone Conversion...\n")
    
    processed = process_files()
    
    print(f"\n✅ Conversion Complete!")
    print(f"Files processed: {len(processed)}")
    if processed:
        print("\nProcessed files:")
        for f in sorted(processed):
            print(f"  • {f}")

