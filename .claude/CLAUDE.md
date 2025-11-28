# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Reaper_BatchConverter 是一个用于自动化 REAPER DAW 批量处理音频文件的 Python 命令行工具。脚本通过外部调用 REAPER 的 **Batch Convert** 功能,应用预设的 **FX Chain (效果链)** 到当前目录下的所有音频文件,处理完成后自动用输出文件替换原文件。

**核心功能**: 外部调用 `reaper.exe -batchconvert` 批量应用音频效果链处理。

## 版本说明

项目包含两个版本：

- **v1.0** (`Reaper_BatchConverter.py`) - 原始版本，路径硬编码在脚本中
- **v2.0** (`Reaper_BatchConverter_v2.py`) - 重构版本 ⭐ **推荐使用**
  - 使用 `pathlib` 现代化路径处理
  - INI 配置文件，无需修改代码
  - 路径清洗与验证（自动检测空格/引号）
  - 命令行参数支持（`--dry-run`, `--backup`, `-d`, `-p` 等）
  - 备份功能
  - 日志系统
  - 自动配置文件生成

详细使用说明见 `USAGE_v2.md`。

## 核心架构

### v1.0 架构（原始版本）

单文件架构，整个程序位于 `Reaper_BatchConverter.py` 中,包含以下核心组件:

1. **配置管理** (`read_config_block_from_file`)
   - 从外部 `.txt` 文件读取 REAPER FX Chain 批处理配置块
   - 配置块包含要应用的效果链设置和批处理参数
   - 提取 `OUTPATTERN` 信息用于识别输出文件命名模式
   - 使用正则表达式: `r'OUTPATTERN\s+\$source([-_\w]*)'`

2. **音频文件扫描** (`get_audio_files_full_paths`)
   - 支持的格式: `.wav`, `.mp3`, `.flac`, `.aiff`, `.ogg`, `.m4a`, `.aif`
   - 返回当前目录下所有音频文件的绝对路径列表

3. **临时配置文件生成** (`generate_config_file`)
   - 组合预设配置块 + 音频文件路径列表
   - 生成临时文件 `batch_config_temp.txt` 供 REAPER 使用

4. **REAPER 批处理调用** (`call_reaper_batch`)
   - 使用 `subprocess.run()` 调用 `reaper.exe -batchconvert <config_file>`
   - 捕获并解码 UTF-8 输出 (使用 `errors='replace'` 处理编码问题)

5. **输出文件替换** (`replace_output_files`)
   - 根据 `OUTPATTERN` 后缀查找 REAPER 生成的文件
   - 删除原始文件并将处理后的文件重命名为原始文件名
   - 实现原地替换逻辑

### 执行流程 (主程序逻辑)

```
用户配置 → 列出预设 → 选择预设 → 读取CONFIG → 校验REAPER路径
→ 扫描音频 → 生成临时配置 → 调用REAPER → 清理临时文件
→ 判断并替换输出 → 结束
```

详细的架构流程图和函数详解见 `architecture.md`。

### v2.0 架构（重构版本）⭐

模块化设计，使用现代 Python 特性：

**核心模块：**
- **配置系统**: `ConfigParser` + `config.ini` 文件
- **路径处理**: 全部使用 `pathlib.Path`
- **路径清洗**: `sanitize_path()` - 去除引号/空格
- **路径验证**: `check_path_for_spaces()` - 检测空格路径
- **日志系统**: `logging` 模块替代 `print`
- **命令行参数**: `argparse` 支持多种运行模式

**新增功能：**
- `load_config()` - 加载/自动生成配置文件
- `backup_files()` - 可选的文件备份功能
- `select_preset()` - 支持交互式或命令行指定预设
- Dry-run 模式 - 预览操作不实际执行

**关键改进：**
- 所有路径使用 `Path` 对象而非字符串
- 自动检测并警告包含空格的路径
- 配置与代码分离，易于维护
- 支持非交互式批量处理脚本集成

## 开发指南

### 运行 v2.0 版本

```bash
# 首次运行（生成配置文件）
python Reaper_BatchConverter_v2.py

# 编辑 config.ini 设置路径后运行
python Reaper_BatchConverter_v2.py

# 命令行参数用法
python Reaper_BatchConverter_v2.py -d /path/to/audio -p PresetName --backup -v
```

### v1.0 配置要求（已过时）

脚本主程序块 (line 121-123) 中有两个必须手动配置的变量:

```python
reaper_exe = r"C:\Program Files\REAPER (x64)\reaper.exe"     # REAPER 可执行文件路径
presets_dir = r"D:\02.Projects_Files\Otoful_PluginPresets\Reaper_Presets"  # 预设配置文件目录
```

## 运行方式

```bash
# 在包含待处理音频文件的目录下运行
cd <包含音频文件的目录>
python D:\MarksFiles\Programming\MarksProgGA\Python\Reaper\Reaper_BatchConverter\Reaper_BatchConverter.py
```

脚本会:
1. 列出 `presets_dir` 中的所有 `.txt` 预设文件
2. 提示用户输入编号选择预设
3. 自动处理当前目录 (`os.getcwd()`) 下的所有音频文件
4. 处理完成后用输出文件替换原始文件

## 关键约束和已知问题

⚠️ **路径空格限制** (见 README.md):
- 脚本无法处理包含空格的音频文件路径
- 即使使用引号包裹也无效
- 这是 REAPER 批处理模式的已知限制

## 预设配置文件格式

预设文件 (`.txt`) 必须包含:
- **REAPER FX Chain 配置**: 定义要应用的音频效果链
- **批处理参数**: 输出格式、采样率、比特深度等设置
- **`OUTPATTERN $source<后缀>`**: 定义输出文件命名模式
  - 例: `OUTPATTERN $source-converted` → 生成 `filename-converted.wav`
  - 例: `OUTPATTERN $source_FX` → 生成 `filename_FX.wav`
  - 如果配置文件未指定,默认使用 `-converted` 后缀

这些预设文件通常从 REAPER 的 Batch Converter 界面导出获得。

## 临时文件管理

脚本会生成并在完成后清理:
- `batch_config_temp.txt`: 临时批处理配置文件
- `batch_config_temp.txt.log`: REAPER 可能生成的日志文件

## 错误处理策略

脚本采用双重验证机制:
1. 检查 `call_reaper_batch` 的返回状态 (`reaper_call_reported_success`)
2. 即使 REAPER 报告错误,仍会检查输出文件是否实际生成
3. 只要找到预期的输出文件就会尝试执行替换操作

## 依赖环境

- Python 3.11.9
- Windows 11
- REAPER DAW (已安装)

**v1.0 依赖:**
- 标准库: `os`, `subprocess`, `shlex`, `time`, `re`

**v2.0 依赖:**
- 标准库: `pathlib`, `subprocess`, `shlex`, `time`, `re`, `sys`, `argparse`, `logging`, `configparser`, `typing`

## 测试与调试

### 使用 Dry-run 模式测试（v2.0）

```bash
# 预览操作而不实际执行
python Reaper_BatchConverter_v2.py --dry-run

# 预览指定目录
python Reaper_BatchConverter_v2.py -d /path/to/audio --dry-run
```

### 详细日志输出

```bash
# 使用 -v 参数查看详细调试信息
python Reaper_BatchConverter_v2.py -v
```

### 路径问题调试

v2.0 会自动检测并报告路径问题：
- 包含空格的路径会被明确标记
- 提供具体的解决方案提示
- 启动时验证所有必需路径的有效性

## 常见开发任务

### 修改配置路径（v2.0）

编辑 `config.ini`：
```ini
[Paths]
reaper_exe = C:/REAPER/reaper.exe
presets_dir = D:/ReaperPresets
```

### 添加新的音频格式支持

在 `get_audio_files()` 函数的 `extensions` 集合中添加新扩展名：
```python
extensions = {".wav", ".mp3", ".flac", ".aiff", ".ogg", ".m4a", ".aif", ".新格式"}
```

### 修改默认输出后缀

**v2.0**: 在 `config.ini` 中设置：
```ini
[Options]
default_output_suffix = -processed
```

**v1.0**: 修改 `Reaper_BatchConverter.py:162` 行的默认值。
