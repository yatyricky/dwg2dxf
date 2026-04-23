# dwg2dxf 构建技能

## 支持的工具链
- CMake 3.10+
- Clang（clang/clang++）
- GCC（g++/gcc）
- MSVC（通过 CMake 生成 VS 项目）

## 构建步骤

```bash
# 1. 进入项目根目录
cd dwg2dxf

# 2. 创建构建目录
mkdir build && cd build

# 3. 使用 Clang 配置（Windows 示例）
cmake .. -G "MinGW Makefiles" -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++
# 或 Linux/macOS:
cmake .. -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++

# 4. 编译
cmake --build . --config Release
```

## 构建产物
- `build/dwg2dxf/dwg2dxf.exe`（Windows）或 `build/dwg2dxf/dwg2dxf`（Linux/macOS）
- `build/fix_dxf.exe` — C++ DXF 后处理工具（编码转换 + 图层颜色修复）

## 已知限制
- `setlocale(LC_ALL, "Chinese-simplified")` 在部分非 Windows 环境可能无效
- 中文编码硬编码为 ANSI_936（GB2312/GBK），不支持其他编码
- **libdxfrw 读取 DWG 的可靠性差**：AC1015 (AutoCAD 2000) 文件因 handle 解析错误导致所有 table control objects 无法找到；AC1021 (AutoCAD 2007) 也读取失败；目前仅确认 AC1018 (AutoCAD 2004) 可正常读取

## 项目迁移历史
- 原项目：Visual Studio 2008（.vcproj / .sln）
- 已迁移：CMakeLists.txt + 修正 include 路径 + Release 模式 + 禁用断言弹窗

## LibreDWG + fix_dxf 生产方案（推荐）
由于 libdxfrw 对旧版 DWG 解析存在深层 bug，实际生产环境使用 **LibreDWG** 进行 DWG→DXF 转换，再用 **C++ fix_dxf** 进行后处理。

### 后处理 fix_dxf 功能
`fix_dxf.exe` 修复 LibreDWG 输出的 DXF 在中文 CAD 查看器中的兼容性问题：
1. **GBK → UTF-8**：LibreDWG 输出 GBK 编码但 header 标记为 AC1021（UTF-8 时代），导致中文乱码。fix_dxf 将内容转为 UTF-8。
2. **修复负图层颜色**：LibreDWG 输出负的 LAYER color 值（如 `-7`），在 CAD 查看器中导致图层不可见（黑屏）。fix_dxf 转为正值。
3. **更新 $DWGCODEPAGE**：将 `ANSI_936` 改为 `UTF-8`。

### 下载 LibreDWG
从 GitHub Release 下载 Windows 64 位预编译包：
```powershell
Invoke-WebRequest -Uri "https://github.com/LibreDWG/libredwg/releases/download/0.13.4/libredwg-0.13.4-win64.zip" -OutFile "libredwg.zip"
Expand-Archive -Path "libredwg.zip" -DestinationPath "."
```

### 完整批量转换（PowerShell）
使用项目根目录的 `start.ps1`：
```powershell
.\start.ps1
```
流程：
1. 用 LibreDWG 将 `secured-dwg/` 下所有 `.dwg` 转为 `.dxf`（输出到 `dxf_fresh/`）
2. 用 `fix_dxf.exe` 处理 `dxf_fresh/` 中的编码和图层颜色
3. 复制处理后的文件到 `dxf_output/`

### 单文件转换
```powershell
.\libredwg-0.13.4-win64\dwg2dxf.exe --as r2007 -y -o output.dxf input.dwg
.\build\fix_dxf.exe .\dxf_fresh
```

### 版本映射
| 参数 | DXF 版本 |
|------|----------|
| `--as r12` | Release 12 |
| `--as r2000` | AutoCAD 2000 |
| `--as r2004` | AutoCAD 2004 |
| `--as r2007` | AutoCAD 2007 |
| `--as r2010` | AutoCAD 2010 |
| `--as r2013` | AutoCAD 2013 |

## 调试技巧
- 在 `libdwgr.cpp` 的 `dwgR` 构造函数中强制设置 `DRW_DBGSL(DRW_dbg::DEBUG)` 可在 Release 模式下输出详细解析日志
- 关键日志：`object map total size`、`WARNING: XXX control not found`、`bad location`
