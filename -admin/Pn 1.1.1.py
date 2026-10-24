#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蜕壳 / Moult — 文件格式批量转换工具
支持任意格式转换，具备完善的同名文件保护与自动备份机制
"""

import os
import sys
import shutil


def get_input(prompt):
    """获取用户输入"""
    return input(prompt).strip()


def generate_unique_name(dirpath, base_name, new_ext):
    """
    生成唯一的文件名，避免覆盖
    例如: a.new → a(1).new → a(2).new
    """
    new_name = os.path.join(dirpath, base_name + new_ext)

    if not os.path.exists(new_name):
        return new_name

    counter = 1
    while True:
        candidate = os.path.join(dirpath, f"{base_name}({counter}){new_ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1
        if counter > 9999:
            raise RuntimeError(f"无法为 {base_name}{new_ext} 生成唯一文件名")


def full_backup(root_path, backup_root):
    """
    完整备份目标文件夹下的所有文件（排除 PapillonBackup 自身）
    保持原目录结构
    """
    print("💾 正在完整备份所有文件...")
    backup_count = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        # 排除 PapillonBackup 文件夹
        if "PapillonBackup" in dirnames:
            dirnames.remove("PapillonBackup")

        for filename in filenames:
            source_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(source_path, root_path)
            backup_path = os.path.join(backup_root, rel_path)
            backup_dir = os.path.dirname(backup_path)

            # 创建备份目录结构
            os.makedirs(backup_dir, exist_ok=True)

            # 如果备份目标已存在，生成唯一名
            if os.path.exists(backup_path):
                dir_name = os.path.dirname(backup_path)
                base_name = os.path.splitext(os.path.basename(backup_path))[0]
                ext = os.path.splitext(backup_path)[1]
                counter = 1
                while True:
                    candidate = os.path.join(dir_name, f"{base_name}({counter}){ext}")
                    if not os.path.exists(candidate):
                        backup_path = candidate
                        break
                    counter += 1
                    if counter > 9999:
                        raise RuntimeError(f"无法为备份文件生成唯一名: {backup_path}")

            shutil.copy2(source_path, backup_path)
            backup_count += 1

    print(f"   共备份 {backup_count} 个文件")
    return backup_count


def batch_rename_files(root_path, old_ext, new_ext, protection_mode, all_target_names):
    """
    批量重命名文件扩展名（备份已在外部完成）

    参数:
        root_path: 根目录路径
        old_ext: 原扩展名（包含点，如 .txt）
        new_ext: 新扩展名（包含点，如 .md）
        protection_mode: 保护模式 ('skip', 'rename', 'overwrite')
        all_target_names: 已计划的目标文件名集合

    返回:
        成功重命名的文件数量
    """
    count = 0
    renamed_files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # 排除 PapillonBackup 文件夹
        if "PapillonBackup" in dirnames:
            dirnames.remove("PapillonBackup")

        for filename in filenames:
            if filename.lower().endswith(old_ext.lower()):
                old_name = os.path.join(dirpath, filename)
                base_name = filename[:-len(old_ext)]
                new_filename = base_name + new_ext
                new_name = os.path.join(dirpath, new_filename)

                # 计算相对于 root_path 的相对路径
                rel_path = os.path.relpath(old_name, root_path)

                # ===== 冲突检测 =====

                # 1. 检查磁盘上是否已有目标文件
                if os.path.exists(new_name):
                    if protection_mode == 'skip':
                        print(f"  ⚠️  跳过（目标文件已存在）: {filename}")
                        continue
                    elif protection_mode == 'rename':
                        new_name = generate_unique_name(dirpath, base_name, new_ext)
                        new_filename = os.path.basename(new_name)
                        print(f"  📝 重命名避免冲突: {filename} → {new_filename}")
                    elif protection_mode == 'overwrite':
                        print(f"  ⚠️  覆盖: {filename} → {new_filename}")

                # 2. 检查是否与本次转换中其他文件的目标名冲突
                rel_new = os.path.relpath(new_name, root_path)
                if rel_new in all_target_names:
                    if protection_mode == 'skip':
                        print(f"  ⚠️  跳过（与其他转换目标冲突）: {filename}")
                        continue
                    elif protection_mode == 'rename':
                        new_name = generate_unique_name(dirpath, base_name, new_ext)
                        new_filename = os.path.basename(new_name)
                        rel_new = os.path.relpath(new_name, root_path)
                        print(f"  📝 重命名避免冲突: {filename} → {new_filename}")
                    elif protection_mode == 'overwrite':
                        print(f"  ⚠️  覆盖（与其他转换目标冲突）: {filename} → {new_filename}")

                all_target_names.add(rel_new)

                try:
                    # 执行重命名（备份已在外部完成）
                    os.rename(old_name, new_name)
                    count += 1
                    renamed_files.append((old_name, new_name))
                    print(f"  ✓ {filename} → {new_filename}")
                except Exception as e:
                    print(f"  ✗ 失败: {filename} - {e}")

    return count, renamed_files


def main():
    print("=" * 60)
    print("     蜕壳 / Moult")
    print("     文件格式批量转换工具")
    print("     支持任意格式转换")
    print("=" * 60)
    print()

    # 第一步：输入路径
    root_path = get_input("📁 请输入目标路径: ")

    # 验证路径
    if not os.path.exists(root_path):
        print(f"\n❌ 错误: 路径不存在: {root_path}")
        sys.exit(1)

    if not os.path.isdir(root_path):
        print(f"\n❌ 错误: 不是有效目录: {root_path}")
        sys.exit(1)

    # 第二步：输入需要转换的扩展名
    old_exts_input = get_input("📄 请输入需要转换的扩展名（多个用空格分隔）: ")
    old_exts = old_exts_input.split()

    for ext in old_exts:
        if not ext.startswith('.'):
            print(f"\n❌ 错误: 扩展名必须以点开头: {ext}")
            sys.exit(1)

    # 第三步：输入目标扩展名
    new_ext = get_input("🔄 请输入转换后的扩展名: ")

    if not new_ext.startswith('.'):
        print(f"\n❌ 错误: 扩展名必须以点开头: {new_ext}")
        sys.exit(1)

    # 第四步：选择保护模式
    print()
    print("🛡️  请选择同名文件保护模式:")
    print("   [1] 跳过 — 遇到同名文件直接跳过（最安全，推荐）")
    print("   [2] 重命名 — 自动添加序号避免冲突（如 file(1).new）")
    print("   [3] 覆盖 — 直接覆盖已有文件（危险！）")

    mode_choice = get_input("   请选择 (1/2/3，默认1): ").strip()

    mode_map = {'1': 'skip', '2': 'rename', '3': 'overwrite'}
    protection_mode = mode_map.get(mode_choice, 'skip')

    mode_desc = {
        'skip': '跳过同名文件',
        'rename': '自动重命名避免冲突',
        'overwrite': '直接覆盖（危险）'
    }

    # 创建备份目录（在目标文件夹之下）
    backup_root = os.path.join(os.path.abspath(root_path), "PapillonBackup")
    os.makedirs(backup_root, exist_ok=True)

    # 确认信息
    print()
    print("-" * 60)
    print("📋 转换信息确认:")
    print(f"   目标路径: {os.path.abspath(root_path)}")
    print(f"   原扩展名: {', '.join(old_exts)}")
    print(f"   新扩展名: {new_ext}")
    print(f"   保护模式: {mode_desc[protection_mode]}")
    print(f"   备份目录: {backup_root}")
    print("-" * 60)

    confirm = get_input("\n⚡ 确认开始转换? (y/n): ")
    if confirm.lower() not in ('y', 'yes', '是'):
        print("\n❎ 已取消操作")
        sys.exit(0)

    # 执行转换
    print()
    print("🚀 开始转换...")
    print(f"💾 备份目录: {backup_root}")
    print()

    # ===== 先完整备份所有文件 =====
    full_backup(root_path, backup_root)
    print()

    total_count = 0
    all_renamed = []
    all_target_names = set()

    for old_ext in old_exts:
        print(f"🔍 正在处理扩展名: {old_ext}")
        count, renamed = batch_rename_files(root_path, old_ext, new_ext, protection_mode, all_target_names)
        total_count += count
        all_renamed.extend(renamed)
        if count > 0:
            print(f"   该格式转换完成: {count} 个文件")
        else:
            print(f"   未找到匹配文件")
        print()

    # 输出结果
    print("=" * 60)
    if total_count > 0:
        print(f"✅ 转换完成! 共转换 {total_count} 个文件")
        print(f"💾 备份位置: {backup_root}")
        print()
        print("📊 转换明细:")
        for old, new in all_renamed:
            old_base = os.path.basename(old)
            new_base = os.path.basename(new)
            print(f"   {old_base} → {new_base}")
        print()
        print("📁 完整备份已保存，可随时恢复")
    else:
        print("⚠️ 未找到任何匹配的文件")
        print(f"💾 但完整备份已保存至: {backup_root}")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❎ 用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)