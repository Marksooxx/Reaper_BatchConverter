# Reaper Batch Converter v2.0 使用说明

## 📋 新版本改进

### ✅ 已实现的优化

1. **现代化路径处理** - 使用 `pathlib` 替代 `os.path`
2. **INI 配置文件** - 路径配置独立存储，无需修改代码
3. **路径清洗与验证** - 自动去除引号，检测空格路径
4. **命令行参数支持** - 支持多种运行模式
5. **备份功能** - 可选的原文件备份
6. **Dry-run 预览模式** - 查看操作而不实际执行
7. **日志系统** - 使用 `logging` 模块，支持详细输出
8. **自动配置生成** - 首次运行自动创建配置模板
9. **智能错误处理** - 针对性错误提示和解决方案
10. **进度提示** - 清晰的操作进度显示

---

## 🚀 快速开始

### 1. 首次运行（生成配置文件）

```bash
python Reaper_BatchConverter_v2.py
```

首次运行会自动创建 `config.ini` 配置文件模板。

### 2. 编辑配置文件

打开 `config.ini`，设置你的路径：

```ini
[Paths]
# ⚠️ 重要：路径中不要包含空格！
reaper_exe = C:/REAPER/reaper.exe
presets_dir = D:/ReaperPresets

[Options]
backup_before_replace = false
backup_dir = .backup
default_output_suffix = -converted
```

**路径配置注意事项：**
- ❌ **不要使用包含空格的路径**（REAPER 限制）
- ❌ 不要用引号包裹路径
- ✅ 使用正斜杠 `/` 或反斜杠 `\` 都可以
- ✅ 推荐使用绝对路径

### 3. 运行批处理

**基本用法（交互式）：**
```bash
# 在包含音频文件的目录下运行
cd /path/to/your/audio/files
python D:/path/to/Reaper_BatchConverter_v2.py
```

程序会：
1. 列出可用的预设文件
2. 让你选择要应用的预设
3. 扫描当前目录的音频文件
4. 调用 REAPER 批处理
5. 自动替换原文件

---

## 🎯 高级用法

### 📁 文件选择模式

v2.0 支持**三种文件选择模式**，优先级：`-f` > `--file-list` > `-d`

#### 模式 1: 处理单个或多个指定文件 ⭐ 新功能

处理单个文件：
```bash
python Reaper_BatchConverter_v2.py -f "audio.wav" -p "Normalize"
```

处理多个文件：
```bash
python Reaper_BatchConverter_v2.py -f "vocal.wav" "bass.wav" "drums.wav" -p "Compress"
```

使用 Shell 通配符（由 Shell 自动展开）：
```bash
# Windows PowerShell
python Reaper_BatchConverter_v2.py -f (Get-ChildItem *.wav) -p "MyPreset"

# Linux/Mac bash
python Reaper_BatchConverter_v2.py -f *.wav -p "MyPreset"
```

支持相对路径和绝对路径：
```bash
# 相对路径（相对当前目录）
python Reaper_BatchConverter_v2.py -f "audio/file1.wav" "audio/file2.wav"

# 绝对路径
python Reaper_BatchConverter_v2.py -f "D:/Audio/file1.wav" "D:/Audio/file2.wav"

# 配合 -d 指定基准目录
python Reaper_BatchConverter_v2.py -d "D:/Audio" -f "file1.wav" "file2.wav"
```

#### 模式 2: 从文件列表读取 ⭐ 新功能

创建文件列表 `files.txt`：
```text
# 我的音频文件列表
vocal_main.wav
vocal_harmony.wav
bass.wav
drums.wav
```

使用文件列表：
```bash
python Reaper_BatchConverter_v2.py --file-list files.txt -p "MyPreset"
```

配合目录参数（列表中使用相对路径）：
```bash
python Reaper_BatchConverter_v2.py --file-list files.txt -d "D:/MyProject/Audio"
```

文件列表格式：
- 每行一个文件路径
- 支持绝对路径和相对路径
- `#` 开头的行为注释
- 空行会被忽略
- 示例文件：`example_filelist.txt`

#### 模式 3: 扫描整个目录（默认）

扫描当前目录：
```bash
python Reaper_BatchConverter_v2.py
```

指定目录：
```bash
python Reaper_BatchConverter_v2.py -d "D:/MyAudioFiles"
```

**通配符过滤** ⭐ 新功能：
```bash
# 只处理 WAV 文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "*.wav"

# 只处理 vocal 开头的文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "vocal*"

# 只处理特定命名的 MP3 文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "mix_*.mp3"
```

### 直接使用指定预设（非交互）

```bash
python Reaper_BatchConverter_v2.py -p "MyPresetName"
```

### 预览模式（Dry Run）

查看将要执行的操作，但不实际修改文件：

```bash
python Reaper_BatchConverter_v2.py --dry-run
```

输出示例：
```
[DRY RUN 模式] 以下是将要执行的操作：
1. 应用预设：Normalize.txt
2. 处理 15 个文件
3. 生成文件后缀：-converted
4. 用处理后的文件替换原文件

要实际执行，请去掉 --dry-run 参数
```

### 备份原文件

在替换前自动备份原文件到 `.backup/` 目录：

```bash
python Reaper_BatchConverter_v2.py --backup
```

或在 `config.ini` 中设置：
```ini
[Options]
backup_before_replace = true
```

### 详细输出模式

显示更多调试信息：

```bash
python Reaper_BatchConverter_v2.py -v
```

### 组合使用

```bash
# 指定目录 + 指定预设 + 备份 + 详细输出
python Reaper_BatchConverter_v2.py -d "D:/Audio" -p "MyPreset" --backup -v

# 预览指定目录的操作
python Reaper_BatchConverter_v2.py -d "D:/Audio" --dry-run
```

---

## 📖 完整命令行参数

```
usage: Reaper_BatchConverter_v2.py [-h] [-f FILES [FILES ...]]
                                   [--file-list FILE_LIST]
                                   [-d DIRECTORY] [--pattern PATTERN]
                                   [-p PRESET] [--dry-run] [--backup]
                                   [-v] [-c CONFIG]

文件选择（优先级：-f > --file-list > -d）：
  -f, --files FILES     指定要处理的音频文件（可指定多个） ⭐
  --file-list FILE      从文本文件读取要处理的文件列表 ⭐
  -d, --directory DIR   音频文件所在目录（默认：当前目录）
  --pattern PATTERN     文件通配符模式（如 "*.wav"），需配合 -d 使用 ⭐

其他参数：
  -h, --help            显示帮助信息
  -p, --preset NAME     预设名称（不含 .txt 扩展名）
  --dry-run             预览模式：显示操作但不执行
  --backup              在替换前备份原文件
  -v, --verbose         详细输出模式
  -c, --config FILE     配置文件路径（默认：config.ini）
```

⭐ = v2.0 新增功能

---

## ⚠️ 重要提醒

### 空格路径问题

REAPER 的 `-batchconvert` 功能**无法处理包含空格的路径**，包括：
- REAPER 可执行文件路径
- 预设目录路径
- 音频文件路径
- 音频文件所在目录路径

**解决方案：**

1. **重新安装 REAPER 到无空格路径**
   ```
   ❌ C:\Program Files\REAPER (x64)\reaper.exe
   ✅ C:\REAPER\reaper.exe
   ```

2. **移动预设目录到无空格路径**
   ```
   ❌ D:\My Documents\REAPER Presets\
   ✅ D:\ReaperPresets\
   ```

3. **移动音频文件到无空格路径**
   ```
   ❌ D:\Audio Files\project 01\
   ✅ D:\AudioFiles\project_01\
   ```

4. **创建符号链接/Junction（高级）**
   ```batch
   # Windows 创建目录 Junction
   mklink /J C:\REAPER "C:\Program Files\REAPER (x64)"
   ```

### 自动检测与提示

v2.0 版本会自动检测路径中的空格并给出明确提示：

```
ERROR: REAPER 可执行文件路径 包含空格：C:\Program Files\REAPER (x64)\reaper.exe
⚠ REAPER 批处理模式无法处理带空格的路径！
   解决方案：
   1. 将文件/目录移动到不含空格的路径
   2. 或创建符号链接/junction 指向无空格路径
```

---

## 🔍 支持的音频格式

- `.wav`
- `.mp3`
- `.flac`
- `.aiff` / `.aif`
- `.ogg`
- `.m4a`

---

## 📂 文件结构

```
Reaper_BatchConverter/
├── Reaper_BatchConverter.py       # 原始版本
├── Reaper_BatchConverter_v2.py    # v2.0 重构版本 ⭐
├── config.ini                     # 配置文件
├── README.md                      # 项目说明
├── USAGE_v2.md                    # v2.0 使用说明（本文件）
├── architecture.md                # 架构文档
└── .backup/                       # 备份目录（使用 --backup 时自动创建）
```

---

## 🆚 v1.0 vs v2.0 对比

| 特性 | v1.0 | v2.0 |
|------|------|------|
| 路径配置 | 硬编码在脚本中 | 独立 INI 配置文件 |
| 路径处理 | `os.path` | `pathlib` ✨ |
| 路径验证 | 无 | 自动检测空格/引号 ✨ |
| 运行模式 | 仅交互式 | 交互式 + 命令行参数 ✨ |
| 备份功能 | 无 | 可选备份 ✨ |
| 预览模式 | 无 | `--dry-run` ✨ |
| 日志系统 | `print` | `logging` 模块 ✨ |
| 错误提示 | 简单 | 详细 + 解决方案 ✨ |
| 配置生成 | 手动创建 | 自动生成模板 ✨ |

---

## 💡 工作流示例

### 场景 1：首次使用

```bash
# 1. 首次运行，生成配置
python Reaper_BatchConverter_v2.py

# 2. 编辑 config.ini，设置路径
notepad config.ini

# 3. 预览运行（不修改文件）
cd D:/MyAudio
python Reaper_BatchConverter_v2.py --dry-run

# 4. 正式运行
python Reaper_BatchConverter_v2.py
```

### 场景 2：批量处理多个项目

```bash
# 项目 1 - 使用 Normalize 预设
python Reaper_BatchConverter_v2.py -d "D:/Project1/Audio" -p "Normalize" --backup

# 项目 2 - 使用 Compress 预设
python Reaper_BatchConverter_v2.py -d "D:/Project2/Audio" -p "Compress" --backup

# 项目 3 - 使用 EQ 预设
python Reaper_BatchConverter_v2.py -d "D:/Project3/Audio" -p "EQ" --backup
```

### 场景 3：自动化脚本

创建 Windows 批处理文件 `process_all.bat`：

```batch
@echo off
set CONVERTER=D:\Tools\Reaper_BatchConverter_v2.py
set PRESET=MyFavoritePreset

python %CONVERTER% -d "D:\Audio\Folder1" -p %PRESET% --backup -v
python %CONVERTER% -d "D:\Audio\Folder2" -p %PRESET% --backup -v
python %CONVERTER% -d "D:\Audio\Folder3" -p %PRESET% --backup -v

echo 全部完成！
pause
```

### 场景 4：只处理特定文件 ⭐ 新功能

```bash
# 只处理人声文件
python Reaper_BatchConverter_v2.py -f "vocal_main.wav" "vocal_harmony.wav" -p "VocalChain"

# 使用文件列表
echo vocal_main.wav > vocals.txt
echo vocal_harmony.wav >> vocals.txt
python Reaper_BatchConverter_v2.py --file-list vocals.txt -p "VocalChain"

# 先预览，确认无误后再执行
python Reaper_BatchConverter_v2.py -f "important.wav" --dry-run
python Reaper_BatchConverter_v2.py -f "important.wav" --backup
```

### 场景 5：按类型分别处理 ⭐ 新功能

```bash
# 只处理 WAV 文件应用降噪
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "*.wav" -p "Denoise"

# 只处理 MP3 文件应用标准化
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "*.mp3" -p "Normalize"

# 只处理混音文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "mix_*.wav" -p "MasterChain"
```

### 场景 6：复杂项目工作流 ⭐ 新功能

```bash
# 步骤 1: 创建要处理的文件列表
cat > process_list.txt << EOF
# 第一轮处理 - 人声
vocals/lead.wav
vocals/harmony1.wav
vocals/harmony2.wav

# 第二轮处理 - 乐器
instruments/bass.wav
instruments/guitar.wav
EOF

# 步骤 2: 预览
python Reaper_BatchConverter_v2.py --file-list process_list.txt -p "MyPreset" --dry-run

# 步骤 3: 执行（带备份）
python Reaper_BatchConverter_v2.py --file-list process_list.txt -p "MyPreset" --backup -v
```

---

## 🐛 故障排除

### 问题：提示路径包含空格

**解决：** 将文件/目录移动到不含空格的路径，或创建符号链接。

### 问题：REAPER 调用失败

**检查：**
1. `config.ini` 中的 `reaper_exe` 路径是否正确
2. REAPER 是否已正确安装
3. 使用 `-v` 参数查看详细错误信息

### 问题：找不到预设文件

**检查：**
1. `config.ini` 中的 `presets_dir` 路径是否正确
2. 预设目录中是否有 `.txt` 文件
3. 预设文件是否从 REAPER 的 Batch Converter 正确导出

### 问题：未生成输出文件

**可能原因：**
1. REAPER 处理失败（查看 REAPER 输出）
2. 预设配置有误
3. 音频文件格式不支持

---

## 📝 版本历史

### v2.0.0 (2025-01-28)
- ✨ 重构代码，使用 pathlib
- ✨ INI 配置文件支持
- ✨ 路径清洗与验证
- ✨ 命令行参数支持
- ✨ 备份功能
- ✨ Dry-run 预览模式
- ✨ 日志系统
- ✨ 智能错误处理

### v1.0.0 (初始版本)
- 基础批处理功能

---

## 🔗 相关链接

- [REAPER 官网](https://www.reaper.fm/)
- [REAPER 用户手册](https://www.reaper.fm/userguide.php)
- [项目 GitHub](https://github.com/yourname/reaper-batch-converter)

---

## 📧 反馈与支持

如有问题或建议，请通过以下方式反馈：
- GitHub Issues
- 邮件联系

---

**享受批量处理的便利！** 🎵
