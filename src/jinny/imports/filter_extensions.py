#!/usr/bin/env python3

import os
import sys
import random
import string
import base64

AnsiMap = {
  'end': '0',
  'normal': '0',
  'bold': '1',
  'faint': '2',
  'italic': '3',
  'underline': '4',
  'blink': '5',
  'fastblink': '6',
  'strikethrough': '9',
  'framed': '51',
  'circled': '52',
  'overlined': '53',
  'black': '30',
  'red': '31',
  'green': '32',
  'yellow': '33',
  'blue': '34',
  'magenta': '35',
  'cyan': '36',
  'white': '37',
  'bg-black': '40',
  'bg-red': '41',
  'bg-green': '42',
  'bg-yellow': '43',
  'bg-blue': '44',
  'bg-magenta': '45',
  'bg-cyan': '46',
  'bg-white': '47',
  'brightblack': '90',
  'brightred': '91',
  'brightgreen': '92',
  'brightyellow': '93',
  'brightblue': '94',
  'brightmagenta': '95',
  'brightcyan': '96',
  'brightwhite': '97',
  'bg-brightblack': '100',
  'bg-brightred': '101',
  'bg-brightgreen': '102',
  'bg-brightyellow': '103',
  'bg-brightblue': '104',
  'bg-brightmagenta': '105',
  'bg-brightcyan': '106',
  'bg-brightwhite': '107',
}

def file_content(filename):
  if os.path.exists(filename):
    dest = filename
  elif os.path.exists(os.path.abspath(filename)):
    dest = os.path.abspath(filename)
  else:
    raise Exception(f"jinny.filter_extenions.file_content(): The file at path {filename} does not exist!")
  try:
    d = open(dest, "r")
    t = d.read()
    d.close()
    return t
  except Exception as e:
    print(f"jinny.filter_extenions.file_content(): Failed to read from file {filename} with exception")
    raise

def print_stdout(content, end:str="\n"):
  print(content, end=end)
  return ""

def print_stderr(content, end:str="\n"):
  sys.stderr.write(content + end)
  sys.stderr.flush()
  return ""

def tee(content, end:str="\n"):
  print(content + end)
  return content

def basename(path:str):
  return os.path.basename(path)

def dirname(path:str):
  return os.path.dirname(path)

def removeprefix(term:str, prefix:str):
  if len(prefix) > len(term):
    return term
  return term[len(prefix):] if term[0:len(prefix)] == prefix else term

def removesuffix(term:str, suffix:str):
  if len(suffix) > len(term):
    return term
  endpoint = len(term) - len(suffix)
  return term[0:endpoint] if term[endpoint:] == suffix else term

def censor(term:str, except_beginning:int=0, except_end:int=0, vals:list=['*'], fixed_length:int=0):
  if fixed_length > 0:
    return ''.join(random.choice(vals) for x in range(fixed_length))
  l = len(term)
  if l <= (except_beginning + except_end):
    raise Exception(f"jinny.filter_extenions.censor(): Length of value to be censored is {l} excepting {except_beginning} characters at the beginning and {except_end} at the end. These settings would lead to the value not being censored at all!")
  return term[0:except_beginning] + ''.join(random.choice(vals) for x in range(l - except_beginning - except_end)) + term[l-except_end:l]

def decorate(s: str, style:str):
  if style not in AnsiMap:
    raise Exception(f"jinny.filter_extenions.decoration(): The provided decoration '{style}' is not registered as an ansi escape code in Jinny. Please check the documentation!")
  return f'\033[{AnsiMap[style.lower()]}m' + s + '\033[0m'

def b64encode(s: str):
  return base64.b64encode(s.encode()).decode()

def b64decode(s: str):
  return base64.b64decode(s.encode()).decode()

def getext(s: str, period:bool=True):
  root, ext = os.path.splitext(s)
  if not ext:
    raise Exception(f"jinny.filter_extenions.getext(): The provided path '{s}' did not result in an extension found via os.path.splitext(). Please check the documentation!")
  return ext if period else ext.replace('.', '')

def removeext(s: str):
  root, ext = os.path.splitext(s)
  if not root:
    raise Exception(f"jinny.filter_extenions.removeext(): The provided path '{s}' did not result in a usable path via os.path.splitext(). Please check the documentation!")
  return root

def newlinetr(s:str, v:str='<br />'):
  return s.replace("\n", v)

def currency(v, symbol:str='$'):
  f = float(v)
  return symbol + "{:,.2f}".format(f)

