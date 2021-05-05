import math
import json

def middle(left, right):
  return math.floor(left + (right - left) / 2)

def compare(val, blockData, i, left, right):
  start = int(blockData["start"], 16)
  end = int(blockData["end"], 16)
  if start <= val <= end:
    return [i]
  elif start > val:
    return [left, i - 1]
  elif end < val:
    return [i + 1, right]
  else:
    return [1, -1]

def search(lt, val, middle=middle, compare=compare):
  left = 0
  right = len(lt)-1
  result = []
  index = 0
  while left <= right :
    index = middle(left, right)
    result = compare(val, lt[index], index, left, right)
    if len(result) == 1:
      return index
    [left, right] = result
  return -1

blockPath = r".\data\blocks.json"

def getBlocks(path):
  lt = []
  with open(path, "r", encoding="utf-8") as file:
    lt = json.load(file)
  return lt

if __name__ == "__main__":
  blockData = getBlocks(blockPath)
  print(len(blockData))
  result = search(blockData, 0x7f)
  print(result, blockData[result])
