# dwg2dxf 项目备忘录

## 项目概述
- **功能**：将 DWG 文件转换为 DXF（ASCII）格式的 GUI 工具
- **工作方式**：Python + tkinter GUI → 调用 LibreDWG `dwg2dxf.exe` → Python 后处理
- **语言**：Python 3（tkinter GUI）

## 核心特性
- 支持读取 DWG 版本：**AC1.2 到 AC1032**（依赖 LibreDWG）
- 修复 LibreDWG 输出的 DXF 兼容性问题（编码 + 图层颜色）
- 支持**拖放**文件/文件夹到窗口
- 支持**递归目录**批量转换
- 输出 DXF 与源文件**同目录**（`.dwg` → `.dxf`）
- 支持输出版本：r12, r14, r2000, r2004, r2007, r2010, r2013

## 项目结构
```
dwg2dxf/
├── gui.py                     # 主程序：tkinter GUI
├── tkinterdnd2/               # 拖放支持库（本地 bundled）
├── libredwg-0.13.4-win64/     # LibreDWG 预编译二进制
│   └── dwg2dxf.exe
├── start.ps1                  # 命令行批量转换脚本（备用）
├── secured-dwg/               # 源 DWG 文件（保密/大文件，不提交）
├── dwgfile/                   # 示例 DWG 文件（测试用）
└── build/                     # CMake 旧构建产物（不再使用）
```

## 使用方法

### GUI 方式（推荐）
```bash
python gui.py
```
- 拖放 DWG 文件或文件夹到窗口
- 或点击"Select Files"/"Select Folder"按钮
- 点击"Convert to DXF"开始转换
- 转换后的 `.dxf` 文件生成在源 `.dwg` 文件旁边

### 命令行方式（备用）
```powershell
# 单文件
.\libredwg-0.13.4-win64\dwg2dxf.exe --as r2007 -y -o output.dxf input.dwg

# 批量（PowerShell）
.\start.ps1
```

## DXF 后处理（内嵌于 gui.py）

LibreDWG 输出的 DXF 存在两个兼容性问题，gui.py 在转换后自动修复：

### 问题 1：编码标记错误
LibreDWG 输出中文时使用 GBK/GB18030 编码，但 Header 中 `$DWGCODEPAGE` 仍标记为 `ANSI_936`。现代 CAD 查看器（按 AC1021+ 规范）默认以 UTF-8 打开，导致中文乱码。

**fix**：将文件内容从 GBK/GB18030 转码为 UTF-8，并更新 `$DWGCODEPAGE` 为 `UTF-8`。

### 问题 2：图层颜色为负值
LibreDWG 输出的 LAYER 表中 `62` group code 的值为负数（如 `-7`），在 CAD 规范中表示**图层关闭/不可见**，导致打开后全黑。

**fix**：在 LAYER table 中将所有负的 `62` 值取绝对值，使图层可见。

### 实现位置
`gui.py` 中的 `fix_dxf_file()` 函数（第 41-100 行）

## 关键代码位置
- **主程序入口**：`gui.py`
- **后处理逻辑**：`gui.py` → `fix_dxf_file()`
- **LibreDWG 调用**：`gui.py` → `_convert_worker()` → `subprocess.run([LIBRE_DWG_EXE, ...])`

## 历史方案

### libdxfrw（已废弃）
原项目基于 [libdxfrw](https://sourceforge.net/projects/libdxfrw/)，但读取 DWG 可靠性差：
- AC1015 (AutoCAD 2000) 因 handle 解析错误导致所有 table control objects 无法找到
- AC1021 (AutoCAD 2007) 读取失败
- 仅 AC1018 (AutoCAD 2004) 可正常读取

**旧文件已删除**：`dwg2dxf.sln`, `dwg2dxf/`, `libdxfrw/` 等 VS2008/C++ 源码

### C++ fix_dxf（已废弃）
曾用 C++ 编写 `fix_dxf.cpp` 并通过 CMake 编译为 `fix_dxf.exe`。由于项目全面转向 Python GUI，C++ 版本已移除，fix 逻辑直接内嵌到 `gui.py` 中。

## 注意事项
- **LibreDWG 的 `dwg2dxf` 输出不稳定**：同一份 DWG 多次转换得到的原始 DXF 可能存在微小差异（如时间戳、字典顺序），但这不影响 CAD 打开效果
- `tkinterdnd2` 已本地 bundled，无需 pip 安装
- 需要 Python 3.8+（内置 tkinter）
