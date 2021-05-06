import re
import math
import json
import pdb
import os.path
from operator import itemgetter, attrgetter

import regex

BlocksTxtPath = r".\data\Blocks.txt"
NameTxtPath = r".\data\DerivedName.txt"
AliasTxtPath = r".\data\NameAliases.txt"
ScriptsTxtPath = r".\data\Scripts.txt"
PropertyValueAliasesTxtPath = r".\data\PropertyValueAliases.txt"
PropertyAliasesTxtPath = r".\data\PropertyAliases.txt"
BidiBracketsTxtPath = r".\data\BidiBrackets.txt"
BidiMirroringTxtPath = r".\data\BidiMirroring.txt"
BidiClassTxtPath = r".\data\DerivedBidiClass.txt"
UnicodeDataTxtPath = r".\data\UnicodeData.txt"

OutputPath = r".\data\json\block"
OutputBlockPath = r".\data\json\UnicodeBlocks.json"
OutputScriptNamePath = r".\data\json\ScriptName.json"
OutputGeneralCategoryNamePath = r".\data\json\GeneralCategoryName.json"
OutputBinaryPropertyNamePath = r".\data\json\BinaryPropertyName.json"
OutputBidiClassNamePath = r".\data\json\BidiClassName.json"


def toHexNum(val):
  return int(val, 16) if type(val) is str else val


def toHexStr(val):
  return f"{val:04X}"


def middle(left, right):
  return math.floor(left + (right - left) / 2)


def compare(data, val, i, left, right):
  codePoint = toHexNum(data["codePoint"])
  v = toHexNum(val)
  if codePoint == v:
    return [i]
  elif codePoint > v:
    return [left, i - 1]
  elif codePoint < v:
    return [i + 1, right]


def compareBlock(blockData, val, i, left, right):
  start = toHexNum(blockData["start"])
  end = toHexNum(blockData["end"])
  v = toHexNum(val)
  if start <= v <= end:
    return [i]
  elif start > v:
    return [left, i - 1]
  elif end < v:
    return [i + 1, right]
  else:
    return [1, -1]


def compareBlockName(blockName, val, i, left, right):
  v = blockName["long"]
  if val == v:
    return [i]
  elif val < v:
    return [left, i - 1]
  elif val > v:
    return [i + 1, right]


def search(lt, val, compare=compare, middle=middle):
  left = 0
  right = len(lt) - 1
  result = []
  index = 0
  while left <= right:
    index = middle(left, right)
    result = compare(lt[index], val, index, left, right)
    if len(result) == 1:
      return index
    [left, right] = result
  return -1


def uniqueAppend(lt, data):
  if data not in lt:
    lt.append(data)


def changeName(name):
  reName = re.compile("[ -]")
  return reName.sub("_", name)


def getBlockName(data, name):
  # pdb.set_trace()
  index = search(data, name, compareBlockName)
  if index != -1:
    return data[index]
  return {"long": name}


def readBlockName(path):
  reObj = re.compile(r"^blk; (?P<short>[^ \n;]+) +; (?P<long>[^ \n;]+)( +; (?P<alias>.+))?")
  result = []
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        if r["alias"] is None:
          result.append({"short": r["short"], "long": r["long"]})
        else:
          result.append({"short": r["short"], "long": r["long"], "alias": r["alias"]})
      line = file.readline()
  # print(result)
  result.sort(key=itemgetter("long"))
  return result


def readBlocks(path, blockName):
  reObj = re.compile(r"^(?P<start>[0-9a-fA-F]+)\.\.(?P<end>[0-9a-fA-F]+); *(?P<name>.+)")
  result = []
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        data = {"start": r["start"], "end": r["end"]}
        data |= getBlockName(blockName, changeName(r["name"]))
        result.append(data)
      line = file.readline()
  return result


def makeNamesRange(d, start, end, name):
  name = name.rstrip("*")
  for i in range(toHexNum(start), toHexNum(end) + 1):
    codePoint = toHexStr(i)
    d[codePoint] = [f"{name}{codePoint}"]


def readNames(path):
  reObj = re.compile(r"^(?P<codePointStart>[0-9a-fA-F]+)(?:..(?P<codePointEnd>[0-9a-fA-F]+))? *; *(?P<name>[^;\n]+)")
  result = {}
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        if r["codePointEnd"] is None:
          result[r["codePointStart"]] = [r["name"]]  # aliasと処理を統一するためにlistで渡す
        else:
          makeNamesRange(result, r["codePointStart"], r["codePointEnd"], r["name"])
      line = file.readline()
  return result


def readAliases(path):
  reObj = re.compile(r"^(?P<codePoint>[0-9a-fA-F]+);(?P<name>[^;\n]+);(?P<type>.+)")
  result = {}
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        if r["codePoint"] not in result:
          result[r["codePoint"]] = [r["name"]]
        else:
          result[r["codePoint"]].append(r["name"])
      line = file.readline()
  return result

def readBidiMirread(path):
  reObj = re.compile(r"^(?P<codePoint>[0-9a-fA-F]+); (?P<codePointMirred>[0-9a-fA-F]+)")
  result = {}
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        result[r["codePoint"]] = {"mirror": r["codePointMirred"], "type": ""}
      line = file.readline()
  return result

def readBidiBrackets(path, data):
  reObj = re.compile(r"^(?P<codePoint>[0-9a-fA-F]+); (?P<codePointMirred>[0-9a-fA-F]+); (?P<type>.)")
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        t = "open" if r["type"] == "o" else "close"
        data[r["codePoint"]] = {"mirror": r["codePointMirred"], "type": t}
      line = file.readline()
  return data

def readScripts(path):
  reObj = re.compile(r"^(?P<start>[0-9a-fA-F]+)..?(?P<end>[0-9a-fA-F]+)? +; (?P<name>[^; \n]+)")
  result = {}
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        if r["end"] is None:
          result[r["start"]] = r["name"]
        else:
          for i in range(toHexNum(r["start"]), toHexNum(r["end"]) + 1):
            result[toHexStr(i)] = r["name"]
      line = file.readline()
  return result


def readScriptName(path):
  reObj = re.compile(r"^sc ; (?P<short>[^ \n;]+) +; (?P<long>[^ \n;]+)( +; (?P<alias>.+))?")
  result = []
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        if r["alias"] is None:
          result.append({"short": r["short"], "long": r["long"]})
        else:
          result.append({"short": r["short"], "long": r["long"], "alias": r["alias"]})
      line = file.readline()
  return result


def readGeneralCategoryName(path):
  reObj = re.compile(r"^gc ; (?P<short>[^ \n;]+) +; (?P<long>[^ \n;]+)( +; (?P<alias>[^ \n;]+))?")
  result = []
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      r = reObj.search(line)
      if r is not None:
        if r["alias"] is None:
          result.append({"short": r["short"], "long": r["long"]})
        else:
          result.append({"short": r["short"], "long": r["long"], "alias": r["alias"]})
      line = file.readline()
  result.sort(key=itemgetter("short"))
  return result


# 定義が見つからないが有効なもの
def getBinaryInit():
  return [{
      "short": "Any",
      "long": "Any"
  }, {
      "short": "Assigned",
      "long": "Assigned"
  }, {
      "short": "ASCII",
      "long": "ASCII"
  }, {
      "short": "Unassigned",
      "long": "Unassigned"
  }]


def readBinaryPropertyName(path):
  reTitle = re.compile(r"# Binary Properties")
  reObj = re.compile(r"^(?P<short>[^ \n;]+) +; (?P<long>[^ \n;]+)( +; (?P<alias>[^ \n;]+))?")
  dataFlag = False
  result = getBinaryInit()
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    while line != "":
      if not dataFlag:
        r = reTitle.match(line)
        if r is not None:
          dataFlag = True
      else:
        r = reObj.search(line)
        if r is not None:
          if r["alias"] is None:
            result.append({"short": r["short"], "long": r["long"]})
          else:
            result.append({"short": r["short"], "long": r["long"], "alias": r["alias"]})
      line = file.readline()
  result.sort(key=itemgetter("short"))
  return result

def readBidiClassName(path):
  with open(path, "r", encoding="utf-8") as file:
    data = file.read()
  result = []
  reObj = regex.Regex(r"# Bidi_Class=(?P<long>.+)\n\n[0-9a-fA-F]+(\.\.[0-9a-fA-F]+)? *; (?P<short>[^ \n]+)")
  reObj.search(data)
  for match in reObj.matches:
    result.append({"long": match["long"], "short": match["short"]})
  result.sort(key=itemgetter("short"))
  return result

def parseName(name, lt):
  reObj = re.compile(r"([^()\n]+)(?:\((.+)\))?")
  r = reObj.match(name)
  if r is not None:
    for i in range(1, 3):
      if r[i] is not None:
        uniqueAppend(lt, r[i].strip())


def getName(match, name):
  result = []
  if name is None:
    parseName(match["name"], result)
    if match["_alias"] != "":
      parseName(match["_alias"], result)
  else:
    parseName(name, result)
  return result


def getObject(match, name=None, codePoint=None):
  name = getName(match, name)
  if codePoint is None:
    codePoint = match["codePoint"]

  return {
      "codePoint": codePoint,
      "name": name,
      "generalCategory": match["generalCategory"],
      "canonicalCombiningClass": match["canonicalCombiningClass"],
      "bidiClass": match["bidiClass"],
      "decompositionType": match["decompositionType"],
      "numericType1": match["numericType1"],
      "numericType2": match["numericType2"],
      "numericValue": match["numericValue"],
      "bidiMirrored": match["bidiMirrored"],
      "_unknown": match["_unknown"],
      "_capitalLetter": match["_capitalLetter"],
      "_caseFoldingLower": match["_caseFoldingLower"],  # lower
      "_caseFoldingUpper": match["_caseFoldingUpper"],  # upper
  }


def getObjectUndefined(codePoint):
  return {
      "codePoint": codePoint,
      "name": ["undefined"],
      "generalCategory": "",
      "canonicalCombiningClass": "",
      "bidiClass": "",
      "decompositionType": "",
      "numericType1": "",
      "numericType2": "",
      "numericValue": "",
      "bidiMirrored": "",
      "_unknown": "",
      "_capitalLetter": "",
      "_caseFoldingLower": "",
      "_caseFoldingUpper": "",
  }


def makeRange(firstMatch, lastMatch, name):
  result = {}
  for i in range(toHexNum(firstMatch["codePoint"]), toHexNum(lastMatch["codePoint"]) + 1):
    result[toHexStr(i)] = getObject(
        firstMatch,
        f"{name}-{i:X}",
        toHexStr(i),
    )
  return result


def getBlock(data, codePoint):
  index = search(data, codePoint, compareBlock)
  if index != -1:
    return data[index]
  return {"start": "n/a", "end": "n/a", "longName": "unknown"}


def getInfo(data, codePoint):
  try:
    return data[toHexStr(codePoint)]
  except:
    return getObjectUndefined(f"{codePoint:04X}")


def getScript(data, codePoint):
  try:
    return data[toHexStr(codePoint)]
  except:
    return "Unknown"

def getBidiMirroring(data, codePoint):
  try:
    return data[toHexStr(codePoint)]
  except:
    return {}

def readData(path, blockData):
  result = {}
  reBlock = re.compile(
      r"^(?P<codePoint>[0-9a-fA-F]+);(?P<name>[^;]+);(?P<generalCategory>[^;]+);(?P<canonicalCombiningClass>[^;]*);(?P<bidiClass>[^;]*);(?P<decompositionType>[^;]*);(?P<numericType1>[^;]*);(?P<numericType2>[^;]*);(?P<numericValue>[^;]*);(?P<bidiMirrored>[^;]*);(?P<_alias>[^;]*);(?P<_unknown>[^;]*);(?P<_capitalLetter>[^;]*);(?P<_caseFoldingLower>[^;]*);(?P<_caseFoldingUpper>.*)"
  )
  reRange = re.compile(r"<(?P<name>.*), (?P<position>First|Last)>")
  with open(path, "r", encoding="utf-8") as file:
    line = file.readline()
    rangeStart = None
    startName = ""
    while line != "":
      lineMatch = reBlock.search(line)
      if lineMatch is not None:
        rangeMatch = reRange.search(line)
        if rangeMatch is None:
          result[lineMatch["codePoint"]] = getObject(lineMatch)
        else:
          if rangeMatch["position"] == "First":
            rangeStart = lineMatch
            startName = rangeMatch["name"]
          elif rangeMatch["position"] == "Last":
            if (rangeMatch["name"] != startName):
              print(f"invalid data: {lineMatch['codePoint']}")
            else:
              result |= makeRange(rangeStart, lineMatch, startName)
      line = file.readline()
  return result


def setNames(codePoint, data, names):
  cp = toHexStr(codePoint)
  if cp in names:
    for name in names[cp]:
      uniqueAppend(data["name"], name)
  data["name"].sort()


def makeInfo(blockData, basicData, nameData, aliasData, scriptData, bidiData):
  data = []
  for block in blockData:
    start = toHexNum(block["start"])
    end = toHexNum(block["end"])
    for i in range(start, end + 1):
      info = getInfo(basicData, i)
      setNames(i, info, aliasData)
      info["bidiMirrored"] = getBidiMirroring(bidiData, i)
      info["script"] = getScript(scriptData, i)
      info["block"] = block["long"]
      data.append(info)
  return data


def dump(path, data):
  with open(path, "w", encoding="utf-8", newline="\n") as file:
    json.dump(data, file, indent=2)


def dumpUnicodeData(path, data, blockData):
  for block in blockData:
    output = []
    for v in data:
      if v["block"] == block["long"]:
        output.append(v)
    with open(os.path.join(path, f"{block['long']}.json"), "w", encoding="utf-8", newline="\n") as file:
      json.dump(output, file, indent=2)


if __name__ == "__main__":
  # nameData = readNames(NameTxtPath)
  # bidiData = readBidiMirread(BidiMirroringTxtPath)
  # bidiData = readBidiBrackets(BidiBracketsTxtPath, bidiData)
  # blockName = readBlockName(PropertyValueAliasesTxtPath)
  # generalCatetoryName = readGeneralCategoryName(PropertyValueAliasesTxtPath)
  # binaryPropertyName = readBinaryPropertyName(PropertyAliasesTxtPath)
  # blockData = readBlocks(BlocksTxtPath, blockName)
  # aliasData = readAliases(AliasTxtPath)
  # scriptData = readScripts(ScriptsTxtPath)
  # scriptName = readScriptName(PropertyValueAliasesTxtPath)
  # basicData = readData(UnicodeDataTxtPath, blockData)
  bidiName = readBidiClassName(BidiClassTxtPath)
  dump(OutputBidiClassNamePath, bidiName)

  # data = makeInfo(blockData, basicData, nameData, aliasData, scriptData, bidiData)
  # dumpUnicodeData(OutputPath, data, blockData)
  # dump(OutputBlockPath, blockData)
  # dump(OutputScriptNamePath, scriptName)
  # dump(OutputGeneralCategoryNamePath, generalCatetoryName)
  # dump(OutputBinaryPropertyNamePath, binaryPropertyName)