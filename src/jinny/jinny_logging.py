#!/usr/bin/env python3

##############################################
# Imports
import datetime
import json
import sys

##############################################
# Variables
VerboseSetting = True
LoggingLocation = "/dev/stdout"

##############################################
# External Functions
def Log(message, quit:bool=False, quitWithStatus:int=1, AlwaysVerbose:bool=True):
  if AlwaysVerbose == False and VerboseSetting == False:
    return
  if type(message) is dict:
    logToFile(LoggingLocation, f'<{TimeStamp()}> - ' + "\n => ".join([k + ": " + str(message[k]) for k in message]))
  else:
    logToFile(LoggingLocation, f'<{TimeStamp()}> - {message}')

  if quit or quitWithStatus > 1:
    exit(1 * quitWithStatus)

##############################################
# Internal Functions
def TimeStamp():
  return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")

def logToFile(path:str, msg:str):
  if path == "/dev/stdout":
    sys.stdout.write(msg + "\n")
  else:
    with open(path, 'a') as f:
      f.write(msg + "\n")