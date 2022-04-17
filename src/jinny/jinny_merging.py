#!/usr/bin/env python3

import sys

def StandInLogger(f:str):
  return

CombineLists = False
VerboseSetting = 0
LoggingFunction = StandInLogger

def CombineValues(originalVals, newVals, sourceName:str):
  originalType = type(originalVals)
  newType = type(newVals)
  if VerboseSetting > 0:
    LoggingFunction(f'CombineValues(): handling {sourceName}, original item = {originalType!s}, new item = {newType!s}')

  # Easy wins
  if originalType == list and newType == list:
    if VerboseSetting > 0:
      LoggingFunction(f'CombineValues(): found two lists, {"combining and returning" if CombineLists else "replacing old list with new one"}')
    return originalVals + newVals if CombineLists else newVals

  if originalType == None:
    if VerboseSetting > 0:
      LoggingFunction(f'CombineValues(): original item is None, replacing with new item')
    return newVals
  
  if newType == None:
    if VerboseSetting > 0:
      LoggingFunction(f'CombineValues(): new item is None, returning None')
    return None

  # More Common
  if originalType == dict and newType == dict:
    if VerboseSetting > 1:
      LoggingFunction(f'CombineValues(): Handling a dict merge')
    workingVals = originalVals.copy()
    origKeys = originalVals.keys()
    for eleKey, eleVal in newVals.items():
      if eleKey not in origKeys:
        if VerboseSetting > 1:
          LoggingFunction(f'CombineValues(): => Adding new key "{eleKey}"')
        workingVals[eleKey] = eleVal
        continue

      newType = type(eleVal)
      oldType = type(originalVals[eleKey])
      if newType == str or newType == int or newType == bool or newType == float or newType == complex:
        if VerboseSetting > 1:
          LoggingFunction(f'CombineValues(): => Updated value for "{eleKey}"')
        workingVals[eleKey] = eleVal
        continue
      if oldType == list and newType == list:
        if originalVals[eleKey] == newVals[eleKey]:
          if VerboseSetting > 1:
            LoggingFunction(f'CombineValues(): => Key "{eleKey}" is the same list in both old and new, continuing')
        else:
          if VerboseSetting > 1:
            LoggingFunction(f'CombineValues(): => Key "{eleKey}" is an altered list, {"combining and continuing" if CombineLists else "replacing old list with new one"}')
          workingVals[eleKey] = originalVals[eleKey] + newVals[eleKey] if CombineLists else newVals[eleKey]
        continue

      if oldType == dict and newType != dict:
        if VerboseSetting > 1:
          LoggingFunction(f'CombineValues(): => Key "{eleKey}" was a dict but updated to be a {newType!s}, replacing')
        workingVals[eleKey] = newVals[eleKey]
        continue

      if newType == dict and newType == dict:
        if VerboseSetting > 1:
          LoggingFunction(f'CombineValues(): => Key "{eleKey}" is a dict updated with another dict, recursively calling CombineValues to handle')
        res = CombineValues(originalVals[eleKey], newVals[eleKey], sourceName)
        workingVals[eleKey] = res

    return workingVals

def SetNestedValue(baseResource, path:list, value):
  if VerboseSetting > 1:
    LoggingFunction(f'SetNestedValue(): => Handling path {".".join(path)} of {len(path)} items')
  currentTier = baseResource
  for index, element in enumerate(path):
    currentType = type(currentTier)
    if index + 1 >= len(path):
      LoggingFunction(f'SetNestedValue(): => On last element ({index+1}/{len(path)}), setting "{element}" to "{value}"')
      currentTier[element] = value
      break
    if currentType == dict:
      if element in currentTier:
        LoggingFunction(f'SetNestedValue(): => Moving to nested dictionary "{element}"')
        currentTier = currentTier[element]
      else:
        raise Exception(f"Could not find {element} in {baseResource} after cycling through {', '.join(path[:index])}")
    elif currentType == list:
      try:
        location = int(element)
      except:
        execDetails = sys.exc_info()
        LoggingFunction(f"Found a list at location '{'.'.join(path[:index])}' but did not find a number integer in the targeting, ie failed to convert the next element in the path '{element}' to an integer so can't target the list, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
      if location + 1 > len(currentTier):
        LoggingFunction(f"Found a list at location '{'.'.join(path[:index])}' that is {len(currentTier)} items long, however '{location}' is not an existing element, hence can't be targeted! Details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
      LoggingFunction(f'SetNestedValue(): => Moving to nested list property index "{location}"')
      currentTier = currentTier[location]
    elif currentType == str or currentType == int or currentType == bool or currentType == float or currentType == complex:
      if index + 1 >= len(path):
        raise Exception(f"Hit a non-nested type of {currentType} at {index} / {len(path)} after cycling through {', '.join(path[:index])}.\nFull path is {', '.join(path)}.\nTarget Object is:\n{yaml.dump(baseResource)}".encode().decode('unicode-escape'))

def GenerateNestedDict(path:list, value):
  if VerboseSetting > 1:
    LoggingFunction(f'GenerateNestedDict(): => Generating a nested dict {len(path) - 1} levels deep setting "{path[len(path)-1]}" to "{value}"')
  replicatedObj = {}
  target = replicatedObj
  for index, item in enumerate(path):
    if index + 1 == len(path):
      target[item] = value
      break
    target[item] = {}
    target = target[item]
  return replicatedObj
