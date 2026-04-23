<p align="center">
  <h3 align="center">dwg2dxf</h3>
  <p align="center">
    DWG to DXF Converter - GUI application with encoding fix
</p>

功能将 DWG 文件转换为 DXF 文件，修复中文乱码和图层颜色问题。

## 使用方法

### GUI 方式（推荐）

```bash
python gui.py
```

功能：
- 拖放 DWG 文件或文件夹到窗口
- 或点击按钮选择文件/文件夹
- 自动递归查找目录下的所有 DWG 文件
- 转换后的 DXF 文件生成在源文件旁边
- 实时显示转换进度和结果

### 命令行方式（备用）

```powershell
# 批量转换
.\start.ps1
```

## 技术原理

1. **LibreDWG** (`libredwg-0.13.4-win64/dwg2dxf.exe`) 将 DWG 转为 DXF
2. **Python 内置修复**：
   - GBK/GB18030 → UTF-8 编码转换
   - 修复负值图层颜色（使其可见）
   - 更新 `$DWGCODEPAGE` 为 `UTF-8`

## 项目历史

- 原项目基于 libdxfrw（C++），但读取 DWG 可靠性差
- 已迁移为 Python + tkinter GUI，使用 LibreDWG 做转换核心
