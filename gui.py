#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWG to DXF Converter GUI
Uses LibreDWG dwg2dxf.exe + Python post-processing
"""

import os
import sys
import glob
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# ---------------------------------------------------------------------------
# Base directory (supports both script and PyInstaller frozen mode)
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add local tkinterdnd2 to path (bundled, no pip install needed)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME = "DWG to DXF Converter"
# LibreDWG path: PyInstaller onedir puts bundled dirs under _internal/
_libre_paths = [
    os.path.join(BASE_DIR, "libredwg-0.13.4-win64", "dwg2dxf.exe"),
    os.path.join(BASE_DIR, "_internal", "libredwg-0.13.4-win64", "dwg2dxf.exe"),
]
LIBRE_DWG_EXE = next((p for p in _libre_paths if os.path.exists(p)), _libre_paths[0])

# ---------------------------------------------------------------------------
# Fix DXF logic (migrated from fix_dxf.cpp)
# ---------------------------------------------------------------------------

def fix_dxf_file(filepath):
    """Fix a single DXF file: encoding, layer colors, DWGCODEPAGE."""
    with open(filepath, 'rb') as f:
        data = f.read()

    original_size = len(data)

    # Decode as GBK/GB18030
    try:
        text = data.decode('gbk', errors='strict')
        encoding = 'gbk'
    except UnicodeDecodeError:
        try:
            text = data.decode('gb18030', errors='strict')
            encoding = 'gb18030'
        except UnicodeDecodeError:
            try:
                text = data.decode('utf-8', errors='strict')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                text = data.decode('gbk', errors='replace')
                encoding = 'gbk-replace'

    # Fix negative layer colors
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

    # Update DWGCODEPAGE
    text = text.replace(
        '$DWGCODEPAGE\r\n  3\r\nANSI_936',
        '$DWGCODEPAGE\r\n  3\r\nUTF-8'
    )

    # Write back as UTF-8
    new_data = text.encode('utf-8')
    with open(filepath, 'wb') as f:
        f.write(new_data)

    return original_size, len(new_data), encoding, fixed_colors


def find_dwg_files(paths):
    """Given a list of file/dir paths, return all .dwg files."""
    results = []
    for p in paths:
        if os.path.isfile(p) and p.lower().endswith('.dwg'):
            results.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    if f.lower().endswith('.dwg'):
                        results.append(os.path.join(root, f))
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for p in results:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Theme
        self._setup_theme()

        self.files = []  # list of dwg paths
        self.converting = False

        self._build_ui()

        # Check LibreDWG
        if not os.path.exists(LIBRE_DWG_EXE):
            self._log("WARNING: LibreDWG not found at:", LIBRE_DWG_EXE, color="orange")
            self._log("Please download and extract libredwg-0.13.4-win64/ to project directory.", color="orange")

    def _setup_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Microsoft YaHei UI', 10))
        style.configure('TLabel', font=('Microsoft YaHei UI', 10))
        style.configure('Header.TLabel', font=('Microsoft YaHei UI', 14, 'bold'))
        style.configure('Drop.TFrame', background='#f0f4f8')
        style.configure('Drop.TLabel', background='#f0f4f8', font=('Microsoft YaHei UI', 11))

    def _build_ui(self):
        # Header
        header = ttk.Label(self.root, text=APP_NAME, style='Header.TLabel')
        header.pack(pady=(15, 5))

        desc = ttk.Label(self.root, text="Drag & drop DWG files or folders here, or use the buttons below.")
        desc.pack(pady=(0, 10))

        # Drop area (canvas draws dashed border since tk Frame doesn't support it)
        self.drop_frame = tk.Frame(self.root, bg='#f0f4f8', bd=0)
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        self.drop_canvas = tk.Canvas(
            self.drop_frame, bg='#f0f4f8', highlightthickness=2,
            highlightbackground='#a0aec0', highlightcolor='#3182ce'
        )
        self.drop_canvas.pack(fill=tk.BOTH, expand=True)

        # Draw dashed rectangle on canvas
        self.drop_canvas.create_rectangle(
            10, 10, 790, 190, dash=(8, 4), outline='#a0aec0', width=2, tags='border'
        )
        self.drop_canvas.create_text(
            400, 80, text="Drop DWG files or folders here",
            font=('Microsoft YaHei UI', 13), fill='#4a5568', tags='text1'
        )
        self.drop_canvas.create_text(
            400, 115, text="or click Select Files / Select Folder below",
            font=('Microsoft YaHei UI', 11), fill='#718096', tags='text2'
        )

        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Button(btn_frame, text="Select Files", command=self._select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Select Folder", command=self._select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", command=self._clear).pack(side=tk.LEFT, padx=5)

        # File list
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        ttk.Label(list_frame, text="Files to convert:").pack(anchor=tk.W)

        self.file_listbox = tk.Listbox(list_frame, height=6, font=('Consolas', 10))
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # Progress
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=20, pady=(5, 0))

        self.status_label = ttk.Label(self.root, text="Ready")
        self.status_label.pack(anchor=tk.W, padx=20)

        # Convert button
        self.convert_btn = ttk.Button(self.root, text="Convert to DXF", command=self._start_convert)
        self.convert_btn.pack(pady=10)

        # Log
        ttk.Label(self.root, text="Log:").pack(anchor=tk.W, padx=20)
        self.log_text = scrolledtext.ScrolledText(
            self.root, height=8, font=('Consolas', 9), state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Bind drag-and-drop if available
        self.has_dnd = False
        if HAS_DND:
            try:
                self.drop_frame.drop_target_register(DND_FILES)
                self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)
                self.has_dnd = True
                self._log("Drag-and-drop enabled")
            except Exception as e:
                self._log(f"Note: Drag-and-drop not available ({e})")

    def _on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        self._add_paths(paths)

    def _select_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("DWG files", "*.dwg")])
        if paths:
            self._add_paths(paths)

    def _select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self._add_paths([path])

    def _add_paths(self, paths):
        new_files = find_dwg_files(paths)
        for f in new_files:
            if f not in self.files:
                self.files.append(f)
                self.file_listbox.insert(tk.END, os.path.basename(f))
        self.status_label.config(text=f"{len(self.files)} file(s) queued")
        self._log(f"Added {len(new_files)} DWG file(s)")

    def _clear(self):
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.status_label.config(text="Ready")
        self.progress['value'] = 0

    def _log(self, *args, color="black"):
        msg = " ".join(str(a) for a in args)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _start_convert(self):
        if not self.files:
            messagebox.showwarning("No files", "Please add DWG files first.")
            return
        if not os.path.exists(LIBRE_DWG_EXE):
            messagebox.showerror(
                "LibreDWG not found",
                f"LibreDWG executable not found:\n{LIBRE_DWG_EXE}\n\n"
                "Please download from GitHub and extract to project directory."
            )
            return
        if self.converting:
            return

        self.converting = True
        self.convert_btn.config(state=tk.DISABLED)
        self.progress['maximum'] = len(self.files)
        self.progress['value'] = 0

        thread = threading.Thread(target=self._convert_worker, daemon=True)
        thread.start()

    def _convert_worker(self):
        total = len(self.files)
        success = 0
        failed = 0

        for idx, dwg_path in enumerate(self.files, 1):
            self.root.after(0, lambda i=idx, p=dwg_path: self._log(
                f"[{i}/{total}] Converting: {os.path.basename(p)}"
            ))
            self.root.after(0, lambda: self.status_label.config(
                text=f"Converting {idx}/{total}..."
            ))

            dxf_path = os.path.splitext(dwg_path)[0] + ".dxf"
            temp_dxf = dxf_path + ".tmp"

            try:
                # Step 1: LibreDWG conversion
                cmd = [
                    LIBRE_DWG_EXE,
                    "--as", "r2007",
                    "-y",
                    "-o", temp_dxf,
                    dwg_path
                ]
                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    encoding='utf-8', errors='replace'
                )

                if result.returncode != 0 or not os.path.exists(temp_dxf):
                    self.root.after(0, lambda p=dwg_path: self._log(
                        "  FAILED (LibreDWG):", os.path.basename(p), color="red"
                    ))
                    failed += 1
                    continue

                # Step 2: Fix DXF
                orig, new, enc, fixed = fix_dxf_file(temp_dxf)
                self.root.after(0, lambda p=dwg_path, f=fixed: self._log(
                    f"  Fixed {f} layer colors" if f > 0 else "  No layer fixes needed"
                ))

                # Step 3: Move to final location
                if os.path.exists(dxf_path):
                    os.remove(dxf_path)
                os.rename(temp_dxf, dxf_path)

                self.root.after(0, lambda p=dwg_path: self._log(
                    "  OK:", os.path.basename(p), color="green"
                ))
                success += 1

            except Exception as e:
                self.root.after(0, lambda p=dwg_path, e=e: self._log(
                    "  ERROR:", os.path.basename(p), "-", str(e), color="red"
                ))
                failed += 1
            finally:
                if os.path.exists(temp_dxf):
                    os.remove(temp_dxf)
                self.root.after(0, lambda: self.progress.step(1))

        self.root.after(0, lambda: self._conversion_done(success, failed))

    def _conversion_done(self, success, failed):
        self.converting = False
        self.convert_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Done. Success: {success}, Failed: {failed}")
        self._log("=" * 50)
        self._log(f"Conversion complete. Success: {success}, Failed: {failed}")
        if failed == 0:
            messagebox.showinfo("Done", f"All {success} file(s) converted successfully!")
        else:
            messagebox.showwarning(
                "Done",
                f"Success: {success}\nFailed: {failed}\n\nCheck the log for details."
            )


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
