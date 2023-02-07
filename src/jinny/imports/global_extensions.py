#!/usr/bin/env python3

import datetime
import os
import uuid

def time_now(fmt:str="%Y-%m-%dT%H:%M:%S.%f"):
  return datetime.datetime.now(datetime.timezone.utc).strftime(fmt)

def prompt_envvar(var:str):
  if var in os.environ:
    return os.environ[var]
  print(f"Please set variable '{var}':")
  newVal = input()
  if newVal == "":
    raise Exception(f'jinny.global_extensions.prompt_envvar(): Prompted value for environment variable {var} and got an empty string. Exiting!')
  os.environ[var] = newVal
  return newVal

def list_files(directory:str, recursive:bool=False, topdown:bool=True):
  wd = os.path.abspath(directory)
  if not os.path.exists(wd):
    raise Exception(f'jinny.global_extensions.list_files(): The provided directory at "{wd}" does not exist. Exiting!')
  if not os.path.isdir(wd):
    raise Exception(f'jinny.global_extensions.list_files(): The provided directory at "{wd}" exists but is not a directory. Exiting!')
  returningFiles = []
  if not recursive:
    for f in os.listdir(wd):
      if os.path.isfile(f'{wd}/{f}'):
        returningFiles.append(f'{wd}/{f}')
  else:
    for root, dirs, files in os.walk(wd):
      for fi in files:
        returningFiles.append(f'{root}/{fi}')
  return returningFiles

def gen_uuid4():
  return uuid.uuid4()
