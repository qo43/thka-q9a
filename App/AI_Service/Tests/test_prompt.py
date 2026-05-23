from pathlib import Path
import requests

script_dir = Path(__file__).parent.parent
prompt = (script_dir / "Prompts" / "ar_prompt.txt").read_text(encoding="utf-8")

text = "أطلب وقف تنفيذ قرار إداري صادر بحقي لأنه يسبب ضررًا مباشرًا."

final_prompt = f"{prompt}\n{text}"

res = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b-instruct",
        "prompt": final_prompt,
        "stream": False,
        "options": {"temperature": 0.2}
    }
)

print(res.json()["response"])
