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

def GetNestedResource(listOfElements, baseResource, raiseException=False):
  returningResource = None
  currentTier = baseResource
  for index, element in enumerate(listOfElements):
    currentType = type(currentTier)
    if currentType == dict:
      if element in currentTier:
        currentTier = currentTier[element]
      else:
        if raiseException:
          raise Exception(f"Could not find {element} in {baseResource} after cycling through {', '.join(listOfElements[:index])}")
        else:
          break
    elif currentType == list:
      if len(currentTier) > element + 1:
        currentTier = currentTier[element]
    elif currentType == str or currentType == int or currentType == bool or currentType == float or currentType == complex:
      if index + 1 >= len(listOfElements):
        if raiseException:
          exceptionString = f"Hit a non-nested type of {currentType} at {index} / {len(listOfElements)} after cycling through {', '.join(listOfElements[:index])}.\nFull path is {', '.join(listOfElements)}.\nTarget Object is:\n{yaml.dump(baseResource)}".encode().decode('unicode-escape')
          raise Exception(exceptionString)
        else:
          break
    if index + 1 >= len(listOfElements):
      returningResource = currentTier
      break
  return returningResource

def SetNestedResource(value, baseResource, path:list):
  workingPath = list(path)
  searching = True
  currentResource = baseResource
  while searching:
    t = type(currentResource)
    if t == dict:
      if workingPath[0] in currentResource:
        currentResource = currentResource[workingPath[0]]
        workingPath.pop(0)
        continue
    elif t == list:
      try:
        targetInt = int(workingPath[0])
      except Exception as e:
        execDetails = sys.exc_info()
        LoggingFunction(f"Failed to parse integer for value '{workingPath[0]}'. Current object at path '{'.'.join(path[:len(workingPath)+1])}' is a list, hence it needs an integer for targeting the child element, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
