import json

DataPath = r".\data\UnicodeData.json"

def check(path):
  with open(path, "r", encoding="utf-8") as file:
    data = json.load(file)
  for v in data:
    print(f"{v['codePoint']}, {v['name'][0]}, {v['block']['name']}")

check(DataPath)