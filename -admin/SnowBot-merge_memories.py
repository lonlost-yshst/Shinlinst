import json
import os
import glob

def merge_memories():
    # 读取所有旧记忆文件
    old_files = sorted(
        glob.glob("memories/Snowballmem*.json"),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].replace("Snowballmem", ""))
    )
    
    merged = []
    for path in old_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged.append({
                    "user": data["user"],
                    "assistant": data["assistant"]
                })
        except Exception as e:
            print(f"跳过 {path}: {e}")
    
    # 保存到新文件
    with open("Snowballmemories.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已合并 {len(merged)} 条对话记录")
    return merged

if __name__ == "__main__":
    merge_memories()