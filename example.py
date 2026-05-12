import requests
import json

# 1. غیراستریم بدون نمایش thinking (بدون تفکر)
print("1. غیراستریم - بدون تفکر")
response = requests.post(
    "http://127.0.0.1:8000/v1/chat/completions",
    json={
        "messages": [{"content": "خوبی؟"}],
        "stream": False,
        "session_id": "my_session_1"
    }
)
data = response.json()
print(f"[پاسخ]: {data['content']}")
print()

# 2. غیراستریم با نمایش thinking (تفکر فعال)
print("2. غیراستریم - با تفکر فعال")
response = requests.post(
    "http://127.0.0.1:8000/v1/chat/completions",
    json={
        "messages": [{"content": "سلام، چطوری؟"}],
        "stream": False,
        "session_id": "my_session_2"
    }
)
data = response.json()
if "reasoning_content" in data:
    print(f"[تفکر]: {data['reasoning_content']}")
if "content" in data:
    print(f"[پاسخ]: {data['content']}")
print()

# 3. استریم بدون نمایش reasoning_content (بدون تفکر)
print("3. استریم - بدون تفکر")
with requests.post(
    "http://127.0.0.1:8000/v1/chat/completions",
    json={"messages": [{"content": "سلام"}], "stream": True, "session_id": "my_session_3"},
    stream=True
) as r:
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: ") and not line.endswith("[DONE]"):
                chunk = json.loads(line[6:])
                if "content" in chunk:
                    print(chunk["content"], end="", flush=True)
    print("\n")

# 4. استریم با نمایش reasoning_content (تفکر فعال)
print("4. استریم - با تفکر فعال")
thinking_header_printed = False
response_header_printed = False
with requests.post(
    "http://127.0.0.1:8000/v1/chat/completions",
    json={"messages": [{"content": "من کیم؟"}], "stream": True, "session_id": "my_session_4"},
    stream=True
) as r:
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: ") and not line.endswith("[DONE]"):
                chunk = json.loads(line[6:])
                if "reasoning_content" in chunk:
                    if not thinking_header_printed:
                        print("[تفکر]: ")
                        thinking_header_printed = True
                    print(chunk['reasoning_content'], end="", flush=True)
                if "content" in chunk:
                    if not response_header_printed:
                        print("\n[پاسخ]: ")
                        response_header_printed = True
                    print(chunk["content"], end="", flush=True)








