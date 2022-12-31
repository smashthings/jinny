#!/usr/bin/env python3

import datetime

def time_now(fmt:str="%Y-%m-%dT%H:%M:%S.%f"):
  return datetime.datetime.now(datetime.timezone.utc).strftime(fmt)