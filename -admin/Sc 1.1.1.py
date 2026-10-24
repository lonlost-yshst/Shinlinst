import shutil
import re
from pathlib import Path


def get_next_index(target_dir: Path, prefix: str, ext: str) -> int:
    """获取当前目录下第一个可用的序号"""
    idx = 1
    while True:
        if not (target_dir / f"{prefix}-{idx}{ext}").exists():
            return idx
        idx += 1


def process_folder(folder: Path, backup_root: Path, root: Path):
    """处理单个文件夹，返回子文件夹列表供递归"""
    dir_name = folder.name
    pattern = re.compile(rf"^{re.escape(dir_name)}-\d+(\.[^.]*)?$")
    
    files = []
    subdirs = []
    
    for item in folder.iterdir():
        if item.is_dir():
            if item.resolve() == backup_root.resolve():
                continue
            subdirs.append(item)
        elif item.is_file():
            if pattern.match(item.name):
                continue
            files.append(item)
    
    files.sort(key=lambda f: f.stat().st_mtime)
    
    rel = folder.relative_to(root)
    backup_dir = backup_root / rel
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    for f in files:
        shutil.copy2(f, backup_dir / f.name)
    
    for f in files:
        ext = f.suffix
        idx = get_next_index(folder, dir_name, ext)
        new_name = f"{dir_name}-{idx}{ext}"
        
        display = str(f.relative_to(root))
        f.rename(folder / new_name)
        print(f"{display} Rename Successful!")
    
    return subdirs


# ========== 第一步：输入路径 ==========
user_input = input("请输入目标文件夹路径：").strip().strip('"').strip("'")
root = Path(user_input).resolve()

if not root.exists():
    print("错误：路径不存在。")
    exit(1)
if not root.is_dir():
    print("错误：路径不是文件夹。")
    exit(1)

# ========== 第二步：确认开始 ==========
input("路径已确认，按回车键开始执行……")

# ========== 执行 ==========
backup_root = root / "ScrivenerBackup"

stack = [root]
while stack:
    current = stack.pop()
    children = process_folder(current, backup_root, root)
    stack.extend(children)

print("\n全部处理完毕。")