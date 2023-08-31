#!/usr/bin/env python3

import os
import sys
import random
import string

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

