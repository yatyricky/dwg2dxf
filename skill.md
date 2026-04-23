# dwg2dxf 项目技能

## 当前工作流（Python GUI + LibreDWG）

项目完全基于 **LibreDWG** 的预编译 `dwg2dxf.exe` 进行 DWG→DXF 转换，后处理逻辑已集成到 Python GUI 中。

### 运行方式

```bash
python gui.py
```

### 功能
- **拖放支持**：将 DWG 文件或文件夹拖入窗口
- **按钮选择**："Select Files" / "Select Folder"
- **自动处理**：
  - LibreDWG 转换 DWG → DXF（临时文件）
  - Python 后处理：GBK → UTF-8、修复负图层颜色、更新 DWGCODEPAGE
  - 输出到源文件旁边（同目录同名 `.dxf`）
- **进度显示**：进度条 + 日志 + 结果统计

### 依赖
- Python 3.8+
- `tkinter`（Python 标准库）
- `tkinterdnd2`（已 bundl 到项目目录，无需 pip 安装）
- LibreDWG 预编译二进制：`libredwg-0.13.4-win64/dwg2dxf.exe`

### 下载 LibreDWG
```powershell
Invoke-WebRequest -Uri "https://github.com/LibreDWG/libredwg/releases/download/0.13.4/libredwg-0.13.4-win64.zip" -OutFile "libredwg.zip"
Expand-Archive -Path "libredwg.zip" -DestinationPath "."
```

---

## 历史工作流（已废弃）

原项目基于 [libdxfrw](https://sourceforge.net/projects/libdxfrw/) C++ 库，通过 CMake 构建。该方案存在 DWG 解析 bug（AC1015/AC1021 读取失败），已全部移除。

### 废弃的构建步骤
```bash
# 不再使用
cmake -B build -S .
cmake --build build --config Release
```

### 版本映射（LibreDWG）
| 参数 | DXF 版本 |
|------|----------|
| `--as r12` | Release 12 |
| `--as r2000` | AutoCAD 2000 |
| `--as r2004` | AutoCAD 2004 |
| `--as r2007` | AutoCAD 2007 |
| `--as r2010` | AutoCAD 2010 |
| `--as r2013` | AutoCAD 2013 |
