# dwg2dxf 项目备忘录

## 项目概述
- **功能**：将 DWG/DXF 文件转换为 DXF（ASCII 或二进制）格式的命令行工具
- **底层库**：基于 [libdxfrw](https://sourceforge.net/projects/libdxfrw/)（读写 DXF 的 C++ 库）
- **语言**：C++（Visual Studio 项目）

## 核心特性
- 支持读取 DWG 版本：**R12 到 v2010**
- 修复了**中文乱码**问题（强制使用 ANSI_936/GB2312 编码）
- 支持**单文件**和**批量**转换模式
- 支持输出 **ASCII** 或 **二进制** DXF

## 项目结构
```
dwg2dxf/
├── dwg2dxf.sln              # VS 解决方案
├── dwg2dxf/
│   ├── dwg2dxf/
│   │   ├── main.cpp         # 入口程序，命令行参数解析
│   │   ├── dx_iface.cpp/h   # 文件导入导出接口
│   │   └── dx_data.h        # 数据存储结构
│   └── libdxfrw/            # 底层库源码
│       └── src/
└── dwgfile/                 # 示例 DWG 文件（测试用）
```

## 使用方法

### 编译
用 Visual Studio 打开 `dwg2dxf.sln`，编译 Debug 或 Release。会自动链接 `libdxfrw.lib`。

### 命令行语法
```
dwg2dxf <input> [-b] [-y] [-B] <-version> <output>
```

| 参数 | 说明 |
|------|------|
| `<input>` | 待转换的 DWG/DXF 文件路径 |
| `-b` | （可选）输出二进制 DXF |
| `-y` / `-Y` | （可选）输出文件存在时直接覆盖 |
| `-B` | （可选）批量模式，`input` 为文件列表文本 |
| `-version` | 输出版本：`-R12`、`-v2000`、`-v2004`、`-v2007`、`-v2010` |
| `<output>` | 输出 DXF 文件路径（或批量模式下的输出目录） |

### 示例
```bash
# 单文件转 ASCII DXF
dwg2dxf "1A-00.dwg" -v2007 "output.dxf"

# 单文件转二进制 DXF
dwg2dxf "1A-00.dwg" -b -v2010 "output.dxf"

# 批量转换（list.txt 每行一个文件完整路径）
dwg2dxf "list.txt" -B -v2007 "C:\output_folder"
```

## 关键代码位置
- **主程序入口**：`dwg2dxf/dwg2dxf/main.cpp`
- **中文乱码修复**：`libdxfrw/src/intern/drw_textcodec.cpp`（强制 `cp == "ANSI_936"`，使用 `DRW_Table936` 码表）
- **文件读写接口**：`dwg2dxf/dwg2dxf/dx_iface.cpp`

## 构建方式

### Visual Studio (原生)
用 Visual Studio 打开 `dwg2dxf.sln`，编译 Debug 或 Release。

### CMake + Clang/MSVC/GCC
项目已添加 `CMakeLists.txt`，支持跨平台构建：

```bash
# 生成构建系统（以 Clang 为例）
cmake -B build -S . -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++

# 编译
cmake --build build --config Release

# 运行
./build/dwg2dxf
```

生成产物：
- `build/libdxfrw.a`（静态库）
- `build/dwg2dxf`（可执行文件）

## 运行时问题修复
- **断言弹窗禁用**：在 `main.cpp` 中加入 `SetErrorMode` + `_CrtSetReportMode`，并在 `CMakeLists.txt` 默认使用 **Release** 模式，避免 Debug Assertion 弹窗阻塞批量转换。
- **Debug 日志强制开启**：在 `libdwgr.cpp` 构造函数中强制 `DRW_DBGSL(DRW_dbg::DEBUG)`，以便 Release 模式也能输出解析日志到 stderr。

## DWG 读取兼容性测试结果
对 `dwgfile/` 目录下的文件进行批量测试：

| 文件 | 版本 | 结果 | 错误码 |
|------|------|------|--------|
| `1A-00.dwg` | AC1018 (2004) | **成功** | - |
| `1A-1-1.dwg` 等 | AC1015 (2000) | **失败** | 9 (BAD_READ_TABLES) |
| `1-1A-4.dwg` | AC1021 (2007) | **失败** | 6 (BAD_READ_HEADER) |

### 失败根因分析（AC1015）
`readDwgTables` 中所有 control handle（LineType、Layer、Style 等）均无法在 `ObjectMap` 中查找成功。根本原因是 **header 中解析出的 handle 值（如 `0xebeb597e`）与 `ObjectMap` 中的 handle 值（如 `0xcbb0770`）完全不匹配**，说明 `dwgReader15` 的 handle 解码或 object map 解析存在深层 bug。

## LibreDWG 方案（已验证成功）

### 下载
从 [LibreDWG GitHub Releases](https://github.com/LibreDWG/libredwg/releases) 下载 Windows 预编译二进制：
- `libredwg-0.13.4-win64.zip`
- 解压到项目目录 `libredwg-0.13.4-win64/`

### 单文件转换
```bash
libredwg-0.13.4-win64\dwg2dxf.exe --as r2007 -y -o out.dxf input.dwg
```
参数说明：
- `--as r2007`：输出 DXF 版本（支持 r12, r14, r2000, r2004, r2007, r2010, r2013）
- `-y`：覆盖已存在文件
- `-o out.dxf`：指定输出文件

### 批量转换（PowerShell）
```powershell
$exe = "libredwg-0.13.4-win64\dwg2dxf.exe"
$outdir = "dxf_output_libredwg"
New-Item -ItemType Directory -Force -Path $outdir
Get-ChildItem "dwgfile\*.dwg" | ForEach-Object {
    $outfile = Join-Path $outdir ($_.BaseName + ".dxf")
    & $exe --as r2007 -y -o $outfile $_.FullName
}
```

### 批量转换结果
对 `dwgfile/` 目录下 12 个 DWG 文件进行测试，**全部成功转换**：

| 文件 | 版本 | libdxfrw | LibreDWG |
|------|------|----------|----------|
| `1A-00.dwg` | AC1018 (2004) | 成功 | 成功 |
| `1A-1-1.dwg` 等 | AC1015 (2000) | 失败 | **成功** |
| `1-1A-4.dwg` | AC1021 (2007) | 失败 | **成功** |

### 结论
LibreDWG 的解析能力远超 libdxfrw，可直接用于生产环境的批量 DWG->DXF 转换。原 libdxfrw 项目保留用于参考，实际转换任务统一使用 LibreDWG。

## DXF 后处理工具 fix_dxf

由于 LibreDWG 输出的 DXF 存在两个兼容性问题，项目内建了 `fix_dxf.exe` 进行一键修复：

### 问题 1：编码标记错误
LibreDWG 输出中文时使用 GBK/GB18030 编码，但 Header 中 `$DWGCODEPAGE` 仍标记为 `ANSI_936`。现代 CAD 查看器（按 AC1021+ 规范）默认以 UTF-8 打开，导致中文乱码。

**fix**：将文件内容从 GBK 转码为 UTF-8，并更新 `$DWGCODEPAGE` 为 `UTF-8`。

### 问题 2：图层颜色为负值
LibreDWG 输出的 LAYER 表中 `62` group code 的值为负数（如 `-7`），在 CAD 规范中表示**图层关闭/不可见**，导致打开后全黑。

**fix**：在 LAYER table 中将所有负的 `62` 值取绝对值，使图层可见。

### 构建
```bash
cmake -B build -S .
cmake --build build --config Release
# 产物：build/fix_dxf.exe
```

### 使用
```bash
# 处理目录下所有 .dxf 文件（就地修改）
build\fix_dxf.exe dxf_fresh\
```

### 技术细节
- 使用 Windows API `MultiByteToWideChar` / `WideCharToMultiByte` 进行 GBK→UTF-8 转码
- 对无效 GBK 字节采用 U+FFFD (`\xEF\xBF\xBD`) 替换，与 Python `decode('gbk', errors='replace')` 行为一致
- 以二进制模式读写，保留 DXF 标准的 CRLF 换行
- 自动检测 UTF-8（无需转码）和 GBK（需转码）

## 注意事项
- 原生 VS 项目使用 `#pragma comment(lib, ...)` 自动链接 `libdxfrw.lib`（已用 `#ifdef _MSC_VER` 包裹，不影响 Clang/GCC）
- 运行时通过 `setlocale(LC_ALL, "Chinese-simplified")` 设置中文环境
- 原项目为 VS2008 (`.vcproj`) 格式，无法被现代 MSBuild 直接识别
- **LibreDWG 的 `dwg2dxf` 输出不稳定**：同一份 DWG 多次转换得到的原始 DXF 可能存在微小差异（如时间戳、字典顺序），因此完整重新跑 pipeline 后与历史备份的逐字节比对可能不完全一致，但这不影响 CAD 打开效果
