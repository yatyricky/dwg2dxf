<p align="center">
  <h3 align="center">dwg2dxf</h3>
  <p align="center">
    dwg2dxf - Program to convert dwg/dxf to dxf(ascii & binary) 
  <p align="center">
    libDXFrw - Library to read/write DXF files (ascii & binary)
</p>

功能将DWG文件转换为DXF文件，支持DWG的版本:-R12到-v2010,修复中文转换乱码问题。

## 生产环境工作流程（推荐）

由于 libdxfrw 读取 DWG 可靠性差，生产环境使用 **LibreDWG + C++ fix_dxf** 方案：

1. **LibreDWG** (`libredwg-0.13.4-win64/dwg2dxf.exe`) 将 DWG 转为 DXF
2. **fix_dxf.exe** (`build/fix_dxf.exe`) 修复编码和图层颜色：
   - GBK/GB18030 → UTF-8
   - 修复负值图层颜色（使其可见）
   - 更新 `$DWGCODEPAGE` 为 `UTF-8`
3. **start.ps1** 一键执行上述两步

### 构建 fix_dxf
```bash
cmake -B build -S .
cmake --build build --config Release
```

### 批量转换
```powershell
.\start.ps1
```

From:
  [libdxfrw](https://sourceforge.net/projects/libdxfrw/)
