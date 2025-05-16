# === 这是一个用于reaper自动batch处理当前文件夹audio文件的程序 ===
# === v1.0.0 ===

import os
import subprocess
# 用于解析简单的类 shell 语法。它主要用于编写需要解析命令行参数或配置文件的程序。
import shlex
import time
# 导入的是 Python 的正则表达式模块
import re

# === 从外部文件读取 CONFIG 块，保留 OUTPATTERN 信息供后续替换使用 ===
def read_config_block_from_file(config_block_path):
    try:
        with open(config_block_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        outpattern = None
        clean_lines = []
        for line in lines:
            if 'OUTPATTERN' in line:
                match = re.search(r'OUTPATTERN\s+\$source([-_\w]*)', line)
                if match:
                    outpattern = match.group(1)
                clean_lines.append(line)
            else:
                clean_lines.append(line)

        return ''.join(clean_lines), outpattern
    except Exception as e:
        print(f"\n[错误] 无法读取配置块文件: {config_block_path}\n{e}")
        return None, None

# === 扫描音频文件 ===
def get_audio_files_full_paths(directory, extensions=None):
    if extensions is None:
        extensions = {".wav", ".mp3", ".flac", ".aiff", ".ogg", ".m4a", ".aif"}

    audio_files_full_paths = []
    try:
        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            if os.path.isfile(full_path) and os.path.splitext(filename)[1].lower() in extensions:
                audio_files_full_paths.append(os.path.abspath(full_path))
    except Exception as e:
        print(f"在目录 {directory} 中查找文件时出错: {e}")
        return None

    return audio_files_full_paths

# === 替换输出文件（按 OUTPATTERN 匹配） ===
def replace_output_files(audio_file_full_paths, pattern_suffix="-converted"):
    for path in audio_file_full_paths:
        base, ext = os.path.splitext(path)
        generated = base + pattern_suffix + ext
        if os.path.exists(generated):
            try:
                os.remove(path)
                time.sleep(0.1)
                os.rename(generated, path)
                print(f"✔ 已覆盖原文件: {os.path.basename(path)}")
            except Exception as e:
                print(f"❌ 无法替换 {path}: {e}")
        else:
            print(f"⚠ 找不到输出文件: {generated}")

# === 生成配置文件 ===
def generate_config_file(config_filename, audio_file_full_paths, external_config_block):
    if not external_config_block:
        print("\n[错误] 配置块内容为空，无法生成 config 文件。")
        return False

    config_content = external_config_block + "\n" + "\n".join(audio_file_full_paths)

    try:
        with open(config_filename, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"配置文件已生成: {config_filename}")
        return True
    except IOError as e:
        print(f"错误：无法写入配置文件 {config_filename}: {e}")
        return False

# === 执行 REAPER CLI ===
def call_reaper_batch(reaper_exe, config_filename):
    if not os.path.exists(config_filename):
        print(f"错误：找不到配置文件 {config_filename}")
        return False

    command = [reaper_exe, "-batchconvert", config_filename]
    print("将执行命令:", ' '.join(shlex.quote(arg) for arg in command))

    try:
        # 捕获原始字节输出，然后手动解码
        result = subprocess.run(command, check=True, capture_output=True) 
        stdout_decoded = result.stdout.decode('utf-8', errors='replace') if result.stdout else "[无]"
        stderr_decoded = result.stderr.decode('utf-8', errors='replace') if result.stderr else "[无]"

        print("--- REAPER 标准输出 ---")
        print(stdout_decoded)
        print("-----------------------")
        if result.stderr:
            print("--- REAPER 错误输出 ---")
            print(stderr_decoded)
            print("-----------------------")
        print("REAPER 批处理调用成功完成。")
        return True
    except subprocess.CalledProcessError as e:
        # 即使 REAPER 失败，也尝试解码其输出
        stdout_decoded = e.stdout.decode('utf-8', errors='replace') if e.stdout else "[无]"
        stderr_decoded = e.stderr.decode('utf-8', errors='replace') if e.stderr else "[无]"
        print(f"错误：调用 REAPER 时发生错误 (退出码: {e.returncode})")
        print("--- 标准输出 ---", stdout_decoded)
        print("--- 错误输出 ---", stderr_decoded)
        return False
    except Exception as e:
        print(f"执行 REAPER 命令时发生未知错误: {e}")
        return False

if __name__ == '__main__':
    # ----------- 用户可修改以下两行 -----------
    reaper_exe = r"C:\Program Files\REAPER (x64)\reaper.exe"
    presets_dir = r"D:\02.Projects_Files\Otoful_PluginPresets\Reaper_Presets"
    # --------------------------------------------

    audio_directory = os.getcwd()
    print(f"当前应用的文件夹目录: {audio_directory}")

    # 1. 列出所有 .txt 配置文件
    try:
        all_files = sorted(f for f in os.listdir(presets_dir) if f.lower().endswith('.txt'))
    except Exception as e:
        print(f"[错误] 无法访问预设目录: {presets_dir}\n{e}")
        exit(1)

    if not all_files:
        print(f"[提示] 目录下没有找到任何 .txt 配置文件: {presets_dir}")
        exit(1)

    print("可用的 Reaper 预设配置文件：")
    for idx, fname in enumerate(all_files, start=1):
        print(f"  {idx:02d}. {fname}")

    # 2. 用户交互：选择配置文件
    sel = input("\n请输入要加载的预设编号（如 01 或 1）：").lstrip('0')
    try:
        sel_idx = int(sel) - 1
        chosen_file = all_files[sel_idx]
    except (ValueError, IndexError):
        print("[错误] 无效的编号，脚本退出。")
        exit(1)

    external_config_path = os.path.join(presets_dir, chosen_file)
    print(f"\n已选择：{chosen_file}")
    
    # 3. 读取 CONFIG 块
    external_config_block, outpattern_suffix = read_config_block_from_file(external_config_path)
    if external_config_block is None:
        exit(1)

    if not outpattern_suffix:
        outpattern_suffix = "-converted"

    # 4. 准备音频文件列表与临时 config 路径
    config_filename = os.path.join(audio_directory, "batch_config_temp.txt")
    log_filename = config_filename + ".log"

    # 5. 校验 reaper.exe
    if not os.path.exists(reaper_exe):
        print(f"[错误] 找不到 REAPER 可执行文件，请检查路径: {reaper_exe}")
        exit(1)

    # 6. 扫描音频文件
    audio_file_full_paths = get_audio_files_full_paths(audio_directory)
    if not audio_file_full_paths:
        print("错误：目录下未找到任何支持的音频文件。")
        exit(1)

    # 7. 生成临时 config
    if not generate_config_file(config_filename, audio_file_full_paths, external_config_block):
        exit(1)

    # 8. 调用 REAPER 批处理
    print("\n开始调用 REAPER 进行批处理...")
    reaper_call_reported_success = call_reaper_batch(reaper_exe, config_filename)

    # 9. 清理临时文件
    for f in (config_filename, log_filename):
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                print(f"[警告] 无法删除文件 {f}")

    # 10. 替换输出
    attempt_replacement = False
    if reaper_call_reported_success:
        attempt_replacement = True
        print("\nREAPER 调用报告成功。")
    else:
        print("\nREAPER 调用报告错误。正在检查是否已实际生成输出文件...")
        generated_file_actually_exists = False
        for path in audio_file_full_paths:
            base, ext = os.path.splitext(path)
            expected_generated_file = base + outpattern_suffix + ext
            if os.path.exists(expected_generated_file):
                print(f"  发现已生成的输出文件: {os.path.basename(expected_generated_file)}")
                generated_file_actually_exists = True
                break # 找到一个就足够尝试替换了
        
        if generated_file_actually_exists:
            print("  已找到 REAPER 生成的输出文件。将尝试进行文件替换。")
            attempt_replacement = True
        else:
            print("  未发现 REAPER 生成的输出文件。跳过替换步骤。")

    if attempt_replacement:
        # 假设 replace_output_files 会打印自己的成功/失败信息
        replace_output_files(audio_file_full_paths, outpattern_suffix)
        if reaper_call_reported_success:
            print("\n脚本执行完毕，REAPER 调用成功且文件已处理。")
        else:
            print("\n脚本执行完毕。REAPER 调用曾报告错误，但已尝试处理找到的输出文件。请检查结果。")
    else:
        # 此情况意味着 REAPER 失败且未找到输出文件
        print("\n脚本执行完毕，REAPER 调用失败，且未找到输出文件进行处理。")

    input("\n按回车键退出...")
