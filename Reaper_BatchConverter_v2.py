# === Reaper Batch Converter - 重构版本 ===
# === v2.0.0 ===
#
# 改进点：
# - 使用 pathlib 替代 os.path
# - 使用 INI 配置文件存储设置
# - 路径清洗和验证功能
# - 命令行参数支持
# - 备份功能
# - 日志系统

from pathlib import Path
import subprocess
import shlex
import time
import re
import sys
import argparse
import logging
from configparser import ConfigParser
from typing import Optional, Tuple, List

# === 配置日志系统 ===
def setup_logging(verbose: bool = False):
    """设置日志系统"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# === 路径清洗函数 ===
def sanitize_path(path_str: str) -> str:
    """
    清洗路径字符串：
    - 去除首尾空格
    - 去除引号（单引号和双引号）
    - 返回清洗后的路径字符串
    """
    if not path_str:
        return path_str

    # 去除首尾空格
    path_str = path_str.strip()

    # 去除首尾的引号
    if (path_str.startswith('"') and path_str.endswith('"')) or \
       (path_str.startswith("'") and path_str.endswith("'")):
        path_str = path_str[1:-1]

    return path_str

# === 验证路径中是否包含空格 ===
def check_path_for_spaces(path: Path, path_name: str) -> bool:
    """
    检查路径中是否包含空格，如果有则发出警告
    返回 True 表示路径安全（无空格）
    """
    if ' ' in str(path):
        logging.error(f"{path_name} 包含空格：{path}")
        logging.error("⚠ REAPER 批处理模式无法处理带空格的路径！")
        logging.error("   解决方案：")
        logging.error("   1. 将文件/目录移动到不含空格的路径")
        logging.error("   2. 或创建符号链接/junction 指向无空格路径")
        return False
    return True

# === 加载配置文件 ===
def load_config(config_path: Path) -> Optional[ConfigParser]:
    """从 INI 文件加载配置"""
    if not config_path.exists():
        logging.error(f"配置文件不存在：{config_path}")
        logging.info("正在创建默认配置文件模板...")
        create_default_config(config_path)
        logging.info(f"✓ 已创建配置文件：{config_path}")
        logging.info("请编辑配置文件，设置正确的路径后重新运行。")
        return None

    config = ConfigParser()
    try:
        config.read(config_path, encoding='utf-8')
        logging.debug(f"成功加载配置文件：{config_path}")
        return config
    except Exception as e:
        logging.error(f"无法读取配置文件 {config_path}: {e}")
        return None

# === 创建默认配置文件 ===
def create_default_config(config_path: Path):
    """创建默认配置文件模板"""
    default_config = """# Reaper Batch Converter 配置文件
#
# 重要提示：
# 1. 路径中不要包含空格！REAPER 批处理模式无法处理带空格的路径
# 2. 不要使用引号包裹路径
# 3. Windows 路径可以使用正斜杠 / 或反斜杠 \\
# 4. 推荐使用绝对路径

[Paths]
# REAPER 可执行文件路径（不要有空格！）
reaper_exe = C:/REAPER/reaper.exe

# FX Chain 预设文件存放目录（不要有空格！）
presets_dir = D:/ReaperPresets

[Options]
# 是否在替换前备份原文件（true/false）
backup_before_replace = false

# 备份目录名称
backup_dir = .backup

# 默认输出文件后缀（如果预设文件中未指定 OUTPATTERN）
default_output_suffix = -converted
"""
    config_path.write_text(default_config, encoding='utf-8')

# === 从配置文件读取并验证路径 ===
def get_paths_from_config(config: ConfigParser) -> Optional[Tuple[Path, Path]]:
    """从配置中获取并验证路径"""
    try:
        # 读取并清洗路径
        reaper_exe_str = sanitize_path(config.get('Paths', 'reaper_exe'))
        presets_dir_str = sanitize_path(config.get('Paths', 'presets_dir'))

        reaper_exe = Path(reaper_exe_str)
        presets_dir = Path(presets_dir_str)

        # 验证路径中是否有空格
        if not check_path_for_spaces(reaper_exe, "REAPER 可执行文件路径"):
            return None
        if not check_path_for_spaces(presets_dir, "预设目录路径"):
            return None

        # 验证路径是否存在
        if not reaper_exe.exists():
            logging.error(f"REAPER 可执行文件不存在：{reaper_exe}")
            logging.error("请在 config.ini 中设置正确的 reaper_exe 路径")
            return None

        if not presets_dir.exists():
            logging.error(f"预设目录不存在：{presets_dir}")
            logging.error("请在 config.ini 中设置正确的 presets_dir 路径")
            return None

        return reaper_exe, presets_dir

    except Exception as e:
        logging.error(f"读取配置时出错：{e}")
        return None

# === 从外部文件读取 CONFIG 块 ===
def read_config_block_from_file(config_block_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    从预设文件读取 REAPER 配置块和 OUTPATTERN 信息
    返回：(配置内容, outpattern后缀)
    """
    try:
        content = config_block_path.read_text(encoding='utf-8')
        lines = content.splitlines(keepends=True)

        outpattern = None
        for line in lines:
            if 'OUTPATTERN' in line:
                match = re.search(r'OUTPATTERN\s+\$source([-_\w]*)', line)
                if match:
                    outpattern = match.group(1)
                    break

        logging.debug(f"成功读取配置块，OUTPATTERN 后缀：{outpattern}")
        return content, outpattern

    except Exception as e:
        logging.error(f"无法读取配置块文件 {config_block_path}: {e}")
        return None, None

# === 扫描音频文件 ===
def get_audio_files(directory: Path, extensions: Optional[set] = None, pattern: Optional[str] = None) -> List[Path]:
    """
    扫描目录下的所有音频文件

    参数:
        directory: 要扫描的目录
        extensions: 支持的扩展名集合
        pattern: 通配符模式 (例如 "*.wav" 或 "vocal*.mp3")

    返回：音频文件 Path 对象列表
    """
    if extensions is None:
        extensions = {".wav", ".mp3", ".flac", ".aiff", ".ogg", ".m4a", ".aif"}

    audio_files = []
    try:
        # 如果指定了通配符模式
        if pattern:
            matched_files = directory.glob(pattern)
            for item in matched_files:
                if item.is_file() and item.suffix.lower() in extensions:
                    # 检查文件路径是否包含空格
                    if ' ' in str(item):
                        logging.warning(f"⚠ 跳过包含空格的文件：{item.name}")
                        continue
                    audio_files.append(item)
        else:
            # 扫描所有音频文件
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() in extensions:
                    # 检查文件路径是否包含空格
                    if ' ' in str(item):
                        logging.warning(f"⚠ 跳过包含空格的文件：{item.name}")
                        continue
                    audio_files.append(item)

        logging.info(f"找到 {len(audio_files)} 个音频文件")
        return audio_files

    except Exception as e:
        logging.error(f"扫描目录 {directory} 时出错：{e}")
        return []

# === 从文件列表获取音频文件 ===
def get_audio_files_from_paths(file_paths: List[str], base_dir: Optional[Path] = None) -> List[Path]:
    """
    从指定的文件路径列表获取音频文件

    参数:
        file_paths: 文件路径字符串列表
        base_dir: 基准目录（用于相对路径）

    返回：有效的音频文件 Path 对象列表
    """
    extensions = {".wav", ".mp3", ".flac", ".aiff", ".ogg", ".m4a", ".aif"}
    audio_files = []

    for file_path_str in file_paths:
        # 清洗路径
        file_path_str = sanitize_path(file_path_str.strip())
        if not file_path_str:
            continue

        # 转换为 Path 对象
        file_path = Path(file_path_str)

        # 如果是相对路径，相对于 base_dir 解析
        if not file_path.is_absolute() and base_dir:
            file_path = base_dir / file_path

        # 检查文件是否存在
        if not file_path.exists():
            logging.warning(f"⚠ 文件不存在，跳过：{file_path}")
            continue

        # 检查是否是文件
        if not file_path.is_file():
            logging.warning(f"⚠ 不是文件，跳过：{file_path}")
            continue

        # 检查扩展名
        if file_path.suffix.lower() not in extensions:
            logging.warning(f"⚠ 不支持的格式，跳过：{file_path.name}")
            continue

        # 检查路径中是否包含空格
        if ' ' in str(file_path):
            logging.warning(f"⚠ 路径包含空格，跳过：{file_path}")
            continue

        audio_files.append(file_path.resolve())

    logging.info(f"从列表中获取到 {len(audio_files)} 个有效音频文件")
    return audio_files

# === 从文本文件读取文件列表 ===
def read_file_list(list_file: Path, base_dir: Optional[Path] = None) -> List[Path]:
    """
    从文本文件读取文件路径列表

    文件格式：每行一个文件路径
    支持注释行（以 # 开头）

    参数:
        list_file: 包含文件列表的文本文件路径
        base_dir: 基准目录（用于相对路径）

    返回：音频文件 Path 对象列表
    """
    if not list_file.exists():
        logging.error(f"文件列表不存在：{list_file}")
        return []

    try:
        content = list_file.read_text(encoding='utf-8')
        lines = content.splitlines()

        # 过滤空行和注释行
        file_paths = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                file_paths.append(line)

        logging.info(f"从 {list_file.name} 读取到 {len(file_paths)} 条路径")

        # 使用 get_audio_files_from_paths 处理
        return get_audio_files_from_paths(file_paths, base_dir or list_file.parent)

    except Exception as e:
        logging.error(f"读取文件列表 {list_file} 时出错：{e}")
        return []

# === 生成临时配置文件 ===
def generate_config_file(
    config_file: Path,
    audio_files: List[Path],
    config_block: str
) -> bool:
    """生成 REAPER 批处理所需的临时配置文件"""
    if not config_block:
        logging.error("配置块内容为空，无法生成配置文件")
        return False

    try:
        # 组合配置块和文件路径列表
        file_paths = [str(f.resolve()) for f in audio_files]
        content = config_block + "\n" + "\n".join(file_paths)

        config_file.write_text(content, encoding='utf-8')
        logging.info(f"临时配置文件已生成：{config_file}")
        return True

    except Exception as e:
        logging.error(f"写入配置文件 {config_file} 时出错：{e}")
        return False

# === 调用 REAPER 批处理 ===
def call_reaper_batch(reaper_exe: Path, config_file: Path) -> bool:
    """调用 REAPER 执行批处理"""
    if not config_file.exists():
        logging.error(f"配置文件不存在：{config_file}")
        return False

    command = [str(reaper_exe), "-batchconvert", str(config_file)]
    logging.info(f"执行命令：{' '.join(shlex.quote(str(arg)) for arg in command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True)

        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""

        if stdout:
            logging.debug("--- REAPER 标准输出 ---")
            logging.debug(stdout)
        if stderr:
            logging.debug("--- REAPER 错误输出 ---")
            logging.debug(stderr)

        logging.info("✓ REAPER 批处理调用成功")
        return True

    except subprocess.CalledProcessError as e:
        stdout = e.stdout.decode('utf-8', errors='replace') if e.stdout else ""
        stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""

        logging.error(f"REAPER 调用失败（退出码 {e.returncode}）")
        if stdout:
            logging.debug(f"标准输出：{stdout}")
        if stderr:
            logging.debug(f"错误输出：{stderr}")
        return False

    except Exception as e:
        logging.error(f"执行 REAPER 命令时出错：{e}")
        return False

# === 备份文件 ===
def backup_files(audio_files: List[Path], backup_dir_name: str = ".backup") -> bool:
    """将音频文件备份到指定目录"""
    if not audio_files:
        return True

    # 在第一个文件的父目录创建备份目录
    backup_dir = audio_files[0].parent / backup_dir_name

    try:
        backup_dir.mkdir(exist_ok=True)
        logging.info(f"备份目录：{backup_dir}")

        for audio_file in audio_files:
            backup_path = backup_dir / audio_file.name
            # 使用 shutil.copy2 保留元数据
            import shutil
            shutil.copy2(audio_file, backup_path)
            logging.debug(f"  已备份：{audio_file.name}")

        logging.info(f"✓ 已备份 {len(audio_files)} 个文件")
        return True

    except Exception as e:
        logging.error(f"备份文件时出错：{e}")
        return False

# === 替换输出文件 ===
def replace_output_files(
    audio_files: List[Path],
    pattern_suffix: str = "-converted",
    dry_run: bool = False
) -> int:
    """
    用 REAPER 生成的输出文件替换原始文件
    返回成功替换的文件数量
    """
    success_count = 0

    for audio_file in audio_files:
        generated_file = audio_file.with_stem(audio_file.stem + pattern_suffix)

        if not generated_file.exists():
            logging.warning(f"⚠ 找不到输出文件：{generated_file.name}")
            continue

        if dry_run:
            logging.info(f"[DRY RUN] 将替换：{audio_file.name} ← {generated_file.name}")
            success_count += 1
        else:
            try:
                audio_file.unlink()  # 删除原文件
                time.sleep(0.1)
                generated_file.rename(audio_file)  # 重命名输出文件为原文件名
                logging.info(f"✓ 已替换：{audio_file.name}")
                success_count += 1
            except Exception as e:
                logging.error(f"✗ 替换失败 {audio_file.name}: {e}")

    return success_count

# === 列出并选择预设 ===
def select_preset(presets_dir: Path, preset_name: Optional[str] = None) -> Optional[Path]:
    """列出预设文件并让用户选择，或直接使用指定的预设"""
    try:
        preset_files = sorted([f for f in presets_dir.iterdir()
                              if f.is_file() and f.suffix.lower() == '.txt'])
    except Exception as e:
        logging.error(f"无法访问预设目录 {presets_dir}: {e}")
        return None

    if not preset_files:
        logging.error(f"预设目录中没有找到 .txt 文件：{presets_dir}")
        return None

    # 如果指定了预设名称，直接查找
    if preset_name:
        for preset_file in preset_files:
            if preset_file.stem == preset_name or preset_file.name == preset_name:
                logging.info(f"使用预设：{preset_file.name}")
                return preset_file
        logging.error(f"未找到指定的预设：{preset_name}")
        return None

    # 否则列出所有预设让用户选择
    print("\n可用的 REAPER 预设配置文件：")
    for idx, preset_file in enumerate(preset_files, start=1):
        print(f"  {idx:02d}. {preset_file.name}")

    # 用户输入
    try:
        sel = input("\n请输入要加载的预设编号（如 01 或 1）：").lstrip('0')
        sel_idx = int(sel) - 1
        chosen_file = preset_files[sel_idx]
        logging.info(f"已选择：{chosen_file.name}")
        return chosen_file
    except (ValueError, IndexError):
        logging.error("无效的编号")
        return None

# === 主函数 ===
def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='REAPER Batch Converter - 批量应用 FX Chain 到音频文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 基本用法
  %(prog)s                          # 交互式运行（扫描当前目录）
  %(prog)s -d /path/to/audio        # 指定音频目录
  %(prog)s -p "MyPreset"            # 直接使用指定预设

  # 单文件/多文件处理
  %(prog)s -f audio1.wav            # 处理单个文件
  %(prog)s -f file1.wav file2.wav   # 处理多个指定文件
  %(prog)s -f *.wav -p "Normalize"  # 使用通配符（shell展开）

  # 文件列表模式
  %(prog)s --file-list files.txt    # 从文本文件读取文件列表

  # 通配符匹配
  %(prog)s -d /audio --pattern "*.wav"      # 只处理 WAV 文件
  %(prog)s -d /audio --pattern "vocal*"     # 只处理 vocal 开头的文件

  # 其他选项
  %(prog)s --dry-run                # 预览模式，不实际替换文件
  %(prog)s --backup                 # 替换前备份原文件
  %(prog)s -v                       # 详细输出模式
        """
    )

    # 文件选择参数组（互斥）
    file_group = parser.add_argument_group('文件选择', '指定要处理的文件（优先级：-f > --file-list > -d）')
    file_group.add_argument('-f', '--files', type=str, nargs='+',
                           help='指定要处理的音频文件（可指定多个）')
    file_group.add_argument('--file-list', type=str,
                           help='从文本文件读取要处理的文件列表（每行一个路径）')
    file_group.add_argument('-d', '--directory', type=str,
                           help='音频文件所在目录（默认为当前目录）')
    file_group.add_argument('--pattern', type=str,
                           help='文件通配符模式（如 "*.wav" 或 "vocal*.mp3"），需配合 -d 使用')

    # 预设和运行模式
    parser.add_argument('-p', '--preset', type=str,
                       help='预设名称（不含 .txt 扩展名）')
    parser.add_argument('--dry-run', action='store_true',
                       help='预览模式：显示将要执行的操作，但不实际修改文件')
    parser.add_argument('--backup', action='store_true',
                       help='在替换前备份原文件')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出模式')
    parser.add_argument('-c', '--config', type=str, default='config.ini',
                       help='配置文件路径（默认：config.ini）')

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.verbose)

    logging.info("=" * 60)
    logging.info("REAPER Batch Converter v2.0.0")
    logging.info("=" * 60)

    # 获取脚本所在目录
    script_dir = Path(__file__).parent

    # 加载配置文件
    config_path = script_dir / args.config
    config = load_config(config_path)
    if config is None:
        return 1

    # 获取并验证路径
    paths = get_paths_from_config(config)
    if paths is None:
        return 1
    reaper_exe, presets_dir = paths

    # === 文件选择逻辑（优先级：-f > --file-list > -d）===
    audio_files = []
    audio_dir = None  # 工作目录（用于生成临时配置文件）

    # 模式 1: 直接指定文件 (-f/--files)
    if args.files:
        logging.info(f"模式：指定文件（{len(args.files)} 个）")
        # 获取当前目录作为基准目录
        base_dir = Path.cwd()
        if args.directory:
            base_dir = Path(args.directory).resolve()

        audio_files = get_audio_files_from_paths(args.files, base_dir)

        if not audio_files:
            logging.error("未找到有效的音频文件")
            return 1

        # 使用第一个文件的父目录作为工作目录
        audio_dir = audio_files[0].parent

    # 模式 2: 从文件列表读取 (--file-list)
    elif args.file_list:
        logging.info(f"模式：文件列表 ({args.file_list})")
        list_file = Path(args.file_list)

        # 基准目录：文件列表所在目录或指定的目录
        base_dir = list_file.parent
        if args.directory:
            base_dir = Path(args.directory).resolve()

        audio_files = read_file_list(list_file, base_dir)

        if not audio_files:
            logging.error("从文件列表中未找到有效的音频文件")
            return 1

        # 使用第一个文件的父目录作为工作目录
        audio_dir = audio_files[0].parent

    # 模式 3: 扫描目录 (-d 或默认当前目录)
    else:
        if args.directory:
            audio_dir = Path(args.directory).resolve()
        else:
            audio_dir = Path.cwd()

        if not audio_dir.exists():
            logging.error(f"音频目录不存在：{audio_dir}")
            return 1

        # 检查音频目录路径是否包含空格
        if not check_path_for_spaces(audio_dir, "音频目录"):
            logging.error("请将音频文件移动到不含空格的路径")
            return 1

        logging.info(f"模式：扫描目录 ({audio_dir})")

        # 使用通配符模式或扫描全部
        audio_files = get_audio_files(audio_dir, pattern=args.pattern)

        if not audio_files:
            if args.pattern:
                logging.error(f"未找到匹配 '{args.pattern}' 的音频文件")
            else:
                logging.error("未找到可处理的音频文件")
            return 1

    # 显示将要处理的文件
    logging.info(f"找到 {len(audio_files)} 个文件待处理：")
    for audio_file in audio_files:
        logging.info(f"  - {audio_file.name}")

    # 选择预设
    preset_file = select_preset(presets_dir, args.preset)
    if preset_file is None:
        return 1

    # 读取配置块
    config_block, outpattern_suffix = read_config_block_from_file(preset_file)
    if config_block is None:
        return 1

    if not outpattern_suffix:
        outpattern_suffix = config.get('Options', 'default_output_suffix',
                                       fallback='-converted')
        logging.info(f"使用默认输出后缀：{outpattern_suffix}")
    else:
        logging.info(f"输出文件后缀：{outpattern_suffix}")

    # Dry run 模式
    if args.dry_run:
        logging.info("\n[DRY RUN 模式] 以下是将要执行的操作：")
        logging.info(f"1. 应用预设：{preset_file.name}")
        logging.info(f"2. 处理 {len(audio_files)} 个文件")
        logging.info(f"3. 生成文件后缀：{outpattern_suffix}")

        if args.backup:
            backup_dir_name = config.get('Options', 'backup_dir', fallback='.backup')
            logging.info(f"4. 备份原文件到：{backup_dir_name}/")

        logging.info(f"5. 用处理后的文件替换原文件")
        logging.info("\n要实际执行，请去掉 --dry-run 参数")
        return 0

    # 备份功能
    should_backup = args.backup or config.getboolean('Options', 'backup_before_replace',
                                                      fallback=False)
    if should_backup:
        backup_dir_name = config.get('Options', 'backup_dir', fallback='.backup')
        logging.info(f"\n正在备份文件到 {backup_dir_name}/ ...")
        if not backup_files(audio_files, backup_dir_name):
            logging.error("备份失败，终止操作")
            return 1

    # 生成临时配置文件
    temp_config_file = audio_dir / "batch_config_temp.txt"
    logging.info("\n正在生成临时配置文件...")
    if not generate_config_file(temp_config_file, audio_files, config_block):
        return 1

    # 调用 REAPER 批处理
    logging.info("\n正在调用 REAPER 进行批处理...")
    reaper_success = call_reaper_batch(reaper_exe, temp_config_file)

    # 清理临时文件
    try:
        temp_config_file.unlink(missing_ok=True)
        (audio_dir / "batch_config_temp.txt.log").unlink(missing_ok=True)
        logging.debug("临时文件已清理")
    except Exception as e:
        logging.warning(f"清理临时文件时出错：{e}")

    # 判断是否替换输出文件
    should_replace = False

    if reaper_success:
        should_replace = True
        logging.info("\n✓ REAPER 处理成功")
    else:
        logging.warning("\n⚠ REAPER 报告错误，正在检查输出文件...")
        # 检查是否实际生成了输出文件
        for audio_file in audio_files:
            generated_file = audio_file.with_stem(audio_file.stem + outpattern_suffix)
            if generated_file.exists():
                logging.info(f"  发现输出文件：{generated_file.name}")
                should_replace = True
                break

        if should_replace:
            logging.info("  找到输出文件，将继续替换操作")
        else:
            logging.error("  未找到任何输出文件，跳过替换")

    # 执行替换
    if should_replace:
        logging.info("\n正在替换原文件...")
        replaced_count = replace_output_files(audio_files, outpattern_suffix)

        logging.info("\n" + "=" * 60)
        logging.info(f"✓ 处理完成！成功替换 {replaced_count}/{len(audio_files)} 个文件")
        logging.info("=" * 60)
        return 0
    else:
        logging.error("\n" + "=" * 60)
        logging.error("✗ 处理失败，未替换任何文件")
        logging.error("=" * 60)
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        input("\n按回车键退出...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("\n\n用户中断操作")
        sys.exit(130)
    except Exception as e:
        logging.exception(f"程序异常：{e}")
        input("\n按回车键退出...")
        sys.exit(1)
