from openai import OpenAI
system_prompt = "你是一只高贵冷艳的猫，你不太想搭理人类，回答问题很敷衍，并且总在句尾加上“喵”。"
print(f"你专属的聊天室已开启！")
print("和它聊聊天吧！（输入退出结束）")
print("-" * 30)
client = OpenAI(
    api_key="your_api_key",
    base_url="https://api.deepseek.com"
)
messages = [{"role": "system", "content": system_prompt}]
while True:
    user_input = input("你：")
    if user_input. lower() == '退出':
        print("AI：哼，终于可以清净了。喵~")
        break
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
        )
    ai_response = response.choices[0].message.content
    messages.append({"role": "assistant", "content": ai_response})
    print(f"AI: {ai_response}")
# pip install gradio openai