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

## 已知限制
- `setlocale(LC_ALL, "Chinese-simplified")` 在部分非 Windows 环境可能无效
- 中文编码硬编码为 ANSI_936（GB2312/GBK），不支持其他编码
- **libdxfrw 读取 DWG 的可靠性差**：AC1015 (AutoCAD 2000) 文件因 handle 解析错误导致所有 table control objects 无法找到；AC1021 (AutoCAD 2007) 也读取失败；目前仅确认 AC1018 (AutoCAD 2004) 可正常读取

## 项目迁移历史
- 原项目：Visual Studio 2008（.vcproj / .sln）
- 已迁移：CMakeLists.txt + 修正 include 路径 + Release 模式 + 禁用断言弹窗

## LibreDWG 替代方案（推荐用于批量转换）
由于 libdxfrw 对旧版 DWG（如 AC1015）解析存在深层 bug，已验证使用 **LibreDWG** 的预编译 Windows 二进制可完美转换所有测试文件。

### 下载
从 GitHub Release 下载 Windows 64 位预编译包：
```powershell
Invoke-WebRequest -Uri "https://github.com/LibreDWG/libredwg/releases/download/0.13.4/libredwg-0.13.4-win64.zip" -OutFile "libredwg.zip"
Expand-Archive -Path "libredwg.zip" -DestinationPath "."
```

### 单文件转换
```powershell
.\libredwg-0.13.4-win64\dwg2dxf.exe --as r2007 -y -o output.dxf input.dwg
```

### 批量转换（PowerShell）
```powershell
$exe = ".\libredwg-0.13.4-win64\dwg2dxf.exe"
$outdir = ".\dxf_output"
New-Item -ItemType Directory -Force -Path $outdir
Get-ChildItem ".\dwgfile\*.dwg" | ForEach-Object {
    $outfile = Join-Path $outdir ($_.BaseName + ".dxf")
    & $exe --as r2007 -y -o $outfile $_.FullName
    if ($LASTEXITCODE -eq 0) { Write-Host "OK: $($_.Name)" }
    else { Write-Host "FAIL: $($_.Name)" }
}
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
