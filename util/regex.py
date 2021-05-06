import re

class Regex:

  def __init__(self, pattern, flags=0):
    self.pattern = pattern
    self.flags = flags
    self.regex = None
    self.compile()
    self.matches = []

  def __repr__(self):
    return f"{self.pattern}, {self.flags}, {len(self.matches)}"

  def compile(self):
    self.regex = re.compile(self.pattern, self.flags)

  def search(self, text):
    self.matches = []
    match = self.regex.search(text)
    if match is None:
      return

    lastIndex = self.storeMatch(match)
    while len(text) >= lastIndex:
      match = self.regex.search(text[lastIndex:])
      if match is None:
        return
      lastIndex = self.storeMatch(match, lastIndex)
    return

  def storeMatch(self, match, lastIndex=0):
    self.matches.append(match)
    return Regex.getLastIndex(match, lastIndex)

  @staticmethod
  def getLastIndex(match, lastIndex=0):
    end = match.end() + lastIndex
    length = len(match[0])
    return end if length > 0 else end + 1