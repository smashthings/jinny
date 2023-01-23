#!/usr/bin/env python3

import os
import sys

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

