#!/usr/bin/env python3

import os

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
