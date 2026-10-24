import os
import json
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(_BASE_DIR, "Snowballmemories.json")

print("=== 记忆系统诊断 ===")
print(f"1. 工作目录: {_BASE_DIR}")
print(f"2. 记忆文件路径: {MEMORY_FILE}")
print(f"3. 文件存在: {os.path.exists(MEMORY_FILE)}")

if os.path.exists(MEMORY_FILE):
    print(f"4. 文件大小: {os.path.getsize(MEMORY_FILE)} 字节")
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"5. JSON解析成功，类型: {type(data)}")
            print(f"6. 记录条数: {len(data)}")
            if len(data) > 0:
                print(f"7. 第一条记录: {data[0]}")
    except Exception as e:
        print(f"5. JSON解析失败: {e}")

# 测试加载函数
def load_memories(limit=None):
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_memories = [[item["user"], item["assistant"]] for item in data]
            if limit and isinstance(limit, int) and limit > 0:
                return all_memories[-limit:]
            return all_memories
    except Exception as e:
        print(f"加载函数出错: {e}")
        return []

print(f"\n8. 加载测试（limit=10）: {len(load_memories(limit=10))} 条")
print(f"9. 实际内容: {load_memories(limit=10)}")