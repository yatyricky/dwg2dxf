#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix LibreDWG DXF output for CAD viewers:
1. Convert GBK/ANSI_936 content to UTF-8
2. Update $DWGCODEPAGE from ANSI_936 to UTF-8
3. Fix negative LAYER color values (make layers visible)
"""

import os
import sys
import glob
import re

DXF_DIR = r"C:\Users\yatyr\workspace\dwg2dxf\dxf_fresh"

def fix_file(filepath):
    print(f"Processing: {os.path.basename(filepath)}")
    
    # Read raw bytes
    with open(filepath, 'rb') as f:
        data = f.read()
    
    original_size = len(data)
    
    # Step 1: Decode as GBK (LibreDWG outputs GBK for Chinese)
    try:
        text = data.decode('gbk', errors='strict')
        encoding = 'gbk'
    except UnicodeDecodeError:
        try:
            text = data.decode('gb18030', errors='strict')
            encoding = 'gb18030'
        except UnicodeDecodeError:
            print(f"  WARNING: Not valid GBK/GB18030, trying utf-8...")
            try:
                text = data.decode('utf-8', errors='strict')
                encoding = 'utf-8'
                print(f"  Already UTF-8, no conversion needed")
            except UnicodeDecodeError:
                text = data.decode('gbk', errors='replace')
                encoding = 'gbk-replace'
                print(f"  WARNING: Had to use replacement characters")
    
    # Step 2: Fix negative layer colors in LAYER table
    # Pattern: " 62\r\n    -N" after a LAYER entry
    fixed_colors = 0
    lines = text.split('\r\n')
    in_layer_table = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line == 'LAYER':
            in_layer_table = True
        elif line == 'ENDTAB':
            in_layer_table = False
        elif in_layer_table and line.strip() == '62':
            if i + 1 < len(lines):
                color_val = lines[i + 1].strip()
                try:
                    color_int = int(color_val)
                    if color_int < 0:
                        lines[i + 1] = '    ' + str(abs(color_int))
                        fixed_colors += 1
                except ValueError:
                    pass
        i += 1
    
    text = '\r\n'.join(lines)
    
    if fixed_colors > 0:
        print(f"  Fixed {fixed_colors} negative layer colors")
    
    # Step 3: Update DWGCODEPAGE
    text = text.replace('$DWGCODEPAGE\r\n  3\r\nANSI_936', '$DWGCODEPAGE\r\n  3\r\nUTF-8')
    
    # Step 4: Write back as UTF-8
    new_data = text.encode('utf-8')
    
    with open(filepath, 'wb') as f:
        f.write(new_data)
    
    print(f"  {original_size} bytes -> {len(new_data)} bytes ({encoding} -> UTF-8)")
    return True

def main():
    files = glob.glob(os.path.join(DXF_DIR, '*.dxf'))
    if not files:
        print(f"No DXF files found in {DXF_DIR}")
        return 1
    
    print(f"Found {len(files)} DXF files")
    print("="*60)
    
    success = 0
    for filepath in sorted(files):
        try:
            if fix_file(filepath):
                success += 1
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("="*60)
    print(f"Done. {success}/{len(files)} files processed.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
