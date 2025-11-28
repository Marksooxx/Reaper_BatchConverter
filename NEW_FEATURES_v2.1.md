# v2.1 新功能 - 完整版文件选择

## ✨ 新增功能概览

### 🎯 三种文件选择模式

现在 Reaper Batch Converter v2.1 支持**三种灵活的文件选择方式**！

#### 1️⃣ 单文件/多文件指定 (`-f / --files`)

**直接指定要处理的文件，而不是整个文件夹**

```bash
# 单个文件
python Reaper_BatchConverter_v2.py -f "important_audio.wav" -p "MyPreset"

# 多个文件
python Reaper_BatchConverter_v2.py -f "vocal.wav" "bass.wav" "drums.wav" -p "Compress"

# 配合目录参数
python Reaper_BatchConverter_v2.py -d "D:/Audio" -f "file1.wav" "file2.wav"
```

**优势：**
- ✅ 精确控制处理哪些文件
- ✅ 支持相对路径和绝对路径
- ✅ 自动验证文件存在性和格式
- ✅ 自动跳过包含空格的路径

#### 2️⃣ 文件列表模式 (`--file-list`)

**从文本文件读取要处理的文件列表**

创建列表文件 `my_files.txt`：
```text
# 我的处理列表
vocal_main.wav
vocal_harmony.wav
bass.wav
drums.wav
```

使用列表：
```bash
python Reaper_BatchConverter_v2.py --file-list my_files.txt -p "MyPreset"
```

**优势：**
- ✅ 适合大量文件的批处理
- ✅ 支持注释（`#` 开头）
- ✅ 可以保存多个预设列表
- ✅ 易于版本控制和共享
- ✅ 支持相对路径和绝对路径

**示例文件**：`example_filelist.txt`

#### 3️⃣ 通配符过滤 (`--pattern`)

**在目录扫描模式下，使用通配符过滤文件**

```bash
# 只处理 WAV 文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "*.wav"

# 只处理 vocal 开头的文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "vocal*"

# 只处理特定命名模式
python Reaper_BatchConverter_v2.py -d "D:/Audio" --pattern "mix_v*.mp3"
```

**优势：**
- ✅ 快速按类型或命名筛选
- ✅ 支持标准 glob 通配符
- ✅ 配合目录参数使用
- ✅ 避免处理不需要的文件

---

## 🔄 优先级逻辑

当同时指定多个文件选择参数时，按以下优先级：

```
-f/--files  >  --file-list  >  -d/--directory
```

**示例：**
```bash
# 即使指定了 -d，也会优先使用 -f 指定的文件
python Reaper_BatchConverter_v2.py -d "D:/Audio" -f "file1.wav" "file2.wav"
# ↑ 只处理 file1.wav 和 file2.wav
```

---

## 📊 对比：v2.0 vs v2.1

| 功能 | v2.0 | v2.1 |
|------|------|------|
| 扫描整个目录 | ✅ | ✅ |
| 指定单个文件 | ❌ | ✅ **新增** |
| 指定多个文件 | ❌ | ✅ **新增** |
| 文件列表模式 | ❌ | ✅ **新增** |
| 通配符过滤 | ❌ | ✅ **新增** |
| INI 配置 | ✅ | ✅ |
| pathlib | ✅ | ✅ |
| 路径清洗验证 | ✅ | ✅ (增强) |
| Dry-run | ✅ | ✅ |
| 备份功能 | ✅ | ✅ |

---

## 💡 实际应用场景

### 场景 1: 音乐制作 - 分轨处理

```bash
# 只处理人声轨
python Reaper_BatchConverter_v2.py -f "vocal_lead.wav" "vocal_harmony.wav" -p "VocalChain"

# 只处理鼓组
python Reaper_BatchConverter_v2.py --pattern "drum_*" -d "D:/Project/Stems" -p "DrumBus"
```

### 场景 2: 播客后期 - 批量降噪

创建 `podcast_files.txt`：
```text
episode_01_raw.wav
episode_02_raw.wav
episode_03_raw.wav
```

```bash
python Reaper_BatchConverter_v2.py --file-list podcast_files.txt -p "Denoise" --backup
```

### 场景 3: 音频库整理 - 按格式处理

```bash
# 只标准化 WAV 文件
python Reaper_BatchConverter_v2.py -d "D:/AudioLibrary" --pattern "*.wav" -p "Normalize"

# 只压缩 MP3 文件
python Reaper_BatchConverter_v2.py -d "D:/AudioLibrary" --pattern "*.mp3" -p "Compress"
```

### 场景 4: 客户项目 - 指定文件处理

```bash
# 客户要求只处理特定文件
python Reaper_BatchConverter_v2.py \
  -f "ClientAudio_v3.wav" "ClientAudio_alt.wav" \
  -p "ClientMasterChain" \
  --backup \
  --dry-run  # 先预览
```

---

## 🛠️ 技术实现

### 新增函数

1. **`get_audio_files_from_paths()`**
   - 从路径列表获取音频文件
   - 支持相对/绝对路径
   - 自动验证和清洗

2. **`read_file_list()`**
   - 从文本文件读取文件列表
   - 支持注释和空行
   - UTF-8 编码

3. **`get_audio_files()` 增强**
   - 新增 `pattern` 参数
   - 支持 glob 通配符匹配

### 新增命令行参数

```python
-f, --files FILES [FILES ...]  # 指定文件
--file-list FILE_LIST          # 文件列表
--pattern PATTERN              # 通配符模式
```

---

## 📝 快速参考

### 命令模板

```bash
# 单文件
python Reaper_BatchConverter_v2.py -f <FILE> -p <PRESET>

# 多文件
python Reaper_BatchConverter_v2.py -f <FILE1> <FILE2> <FILE3> -p <PRESET>

# 文件列表
python Reaper_BatchConverter_v2.py --file-list <LIST.txt> -p <PRESET>

# 通配符
python Reaper_BatchConverter_v2.py -d <DIR> --pattern "<PATTERN>" -p <PRESET>

# 组合使用
python Reaper_BatchConverter_v2.py \
  --file-list files.txt \
  --backup \
  --dry-run \
  -v
```

---

## 🎉 总结

v2.1 版本让 Reaper Batch Converter 更加**灵活**和**强大**！

**你现在可以：**
- ✅ 处理整个文件夹（v1.0 功能）
- ✅ 处理单个或多个指定文件（v2.1 新增）
- ✅ 从列表文件批量处理（v2.1 新增）
- ✅ 使用通配符筛选文件（v2.1 新增）

**所有模式都支持：**
- 路径验证和清洗
- 空格检测和警告
- Dry-run 预览
- 自动备份
- 详细日志

**开始使用：**
```bash
python Reaper_BatchConverter_v2.py -f "your_audio.wav" -p "YourPreset" --dry-run
```

享受更灵活的批处理体验！🎵
