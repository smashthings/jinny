#!/usr/bin/env python3

import datetime
import os

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
