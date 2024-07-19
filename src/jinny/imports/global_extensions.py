#!/usr/bin/env python3

import datetime
import os
import uuid
import base64

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

def req_envvar(var:str, message_format:str=None, message_format_params:list=[]):
  if var in os.environ:
    return os.environ[var]
  if message_format == None:
    message_format = "Missing required environment variable '{0}'!"
    message_format_params = [var]
  raise Exception(f'jinny.global_extensions.req_envvar(): ' + message_format.format(*message_format_params))

def get_envvar(var:str, default:str=""):
  return os.environ[var] if var in os.environ else default

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

def b64file(path:str):
  t = os.path.abspath(path)
  if not os.path.exists(t):
    raise Exception(f'jinny.global_extensions.b64file(): The provided path at "{t}" does not exist. Exiting!')
  if os.path.isdir(t):
    raise Exception(f'jinny.global_extensions.b64file(): The provided path at "{t}" is a directory, b64file only works with files. Exiting!')
  with open(t, "br") as f:
    d = f.read()
  return base64.b64encode(d).decode()

def is_file(path:str):
  return os.path.isfile(path)

def is_dir(path:str):
  return os.path.isdir(path)

def raise_exception(exc:str="Template raised an exception using the 'raise_exception' function!"):
  raise Exception(exc)

def throw(exc:str="Template threw an exception using the 'throw' function!"):
  raise Exception(exc)

