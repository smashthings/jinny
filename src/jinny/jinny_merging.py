#!/usr/bin/env python3

CombineLists = False
VerboseSetting = 0
LoggingFunction = None

def CombineValues(originalVals, newVals, sourceName:str):
  originalType = type(originalVals)
  newType = type(newVals)

  # Easy wins
  if originalType == list and newType == list:
    if CombineLists:
      return originalVals + newVals if CombineLists else newVals

  if originalType == None:
    return newVals
  
  if newType == None:
    return originalVals

  # More Common
  if originalType == dict and newType == dict:
    workingVals = originalVals.copy()
    origKeys = originalVals.keys()
    for eleKey, eleVal in newVals:
      if eleKey not in origKeys:
        workingVals[eleKey] = eleVal
        continue

      newType = type(eleVal)
      oldType = type(originalVals[eleKey])
      if newType == str or newType == int or newType == bool or newType == float or newType == complex:
        workingVals[eleKey] = eleVal
        continue
      if oldType == list and newType == list:
        workingVals[eleKey] = originalVals[eleKey] + newVals[eleKey] if CombineLists else newVals[eleKey]
        continue

      if oldType == dict and newType != dict:
        workingVals[eleKey] = newVals[eleKey]
        continue

      if newType == dict and newType == dict:
        res = CombineValues(originalVals[eleKey], newVals[eleKey], sourceName)
        workingVals[eleKey] = res

    return workingVals

