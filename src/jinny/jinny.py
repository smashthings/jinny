#!/usr/bin/env python3

##########################################
# Imports

import os
import sys
import datetime
import json
import yaml
import jinja2
import argparse
import traceback

baseDir = os.path.dirname(os.path.abspath(__file__))

with open(f'{baseDir}/version') as f:
  __version__ = f.read()

##########################################
# Variables

globalAllTemplatesProcessed = {}
baseJ2Env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
CombineLists = False
VerboseSetting = 0
LoggingLocation = "/dev/stdout"

##########################################
# Machinery
def CombineValues(originalVals, newVals, sourceName:str):
  originalType = type(originalVals)
  newType = type(newVals)
  if VerboseSetting > 0:
    print(VerboseSetting)
    Log(f'CombineValues(): handling {sourceName}, original item = {originalType!s}, new item = {newType!s}')

  # Easy wins
  if originalType == list and newType == list:
    if VerboseSetting > 0:
      Log(f'CombineValues(): found two lists, {"combining and returning" if CombineLists else "replacing old list with new one"}')
    return originalVals + newVals if CombineLists else newVals

  if originalType == None:
    if VerboseSetting > 0:
      Log(f'CombineValues(): original item is None, replacing with new item')
    return newVals
  
  if newType == None:
    if VerboseSetting > 0:
      Log(f'CombineValues(): new item is None, returning None')
    return None

  # More Common
  if originalType == dict and newType == dict:
    if VerboseSetting > 1:
      Log(f'CombineValues(): Handling a dict merge')
    workingVals = originalVals.copy()
    origKeys = originalVals.keys()
    for eleKey, eleVal in newVals.items():
      if eleKey not in origKeys:
        if VerboseSetting > 1:
          Log(f'CombineValues(): => Adding new key "{eleKey}"')
        workingVals[eleKey] = eleVal
        continue

      newType = type(eleVal)
      oldType = type(originalVals[eleKey])
      if newType == str or newType == int or newType == bool or newType == float or newType == complex:
        if VerboseSetting > 1:
          Log(f'CombineValues(): => Updated value for "{eleKey}"')
        workingVals[eleKey] = eleVal
        continue
      if oldType == list and newType == list:
        if originalVals[eleKey] == newVals[eleKey]:
          if VerboseSetting > 1:
            Log(f'CombineValues(): => Key "{eleKey}" is the same list in both old and new, continuing')
        else:
          if VerboseSetting > 1:
            Log(f'CombineValues(): => Key "{eleKey}" is an altered list, {"combining and continuing" if CombineLists else "replacing old list with new one"}')
          workingVals[eleKey] = originalVals[eleKey] + newVals[eleKey] if CombineLists else newVals[eleKey]
        continue

      if oldType == dict and newType != dict:
        if VerboseSetting > 1:
          Log(f'CombineValues(): => Key "{eleKey}" was a dict but updated to be a {newType!s}, replacing')
        workingVals[eleKey] = newVals[eleKey]
        continue

      if newType == dict and newType == dict:
        if VerboseSetting > 1:
          Log(f'CombineValues(): => Key "{eleKey}" is a dict updated with another dict, recursively calling CombineValues to handle')
        res = CombineValues(originalVals[eleKey], newVals[eleKey], sourceName)
        workingVals[eleKey] = res

    return workingVals

def SetNestedValue(baseResource, path:list, value):
  if VerboseSetting > 1:
    Log(f'SetNestedValue(): => Handling path {".".join(path)} of {len(path)} items')
  currentTier = baseResource
  for index, element in enumerate(path):
    currentType = type(currentTier)
    if index + 1 >= len(path):
      Log(f'SetNestedValue(): => On last element ({index+1}/{len(path)}), setting "{element}" to "{value}"')
      currentTier[element] = value
      break
    if currentType == dict:
      if element in currentTier:
        Log(f'SetNestedValue(): => Moving to nested dictionary "{element}"')
        currentTier = currentTier[element]
      else:
        raise Exception(f"Could not find {element} in {baseResource} after cycling through {', '.join(path[:index])}")
    elif currentType == list:
      try:
        location = int(element)
      except:
        execDetails = sys.exc_info()
        Log(f"Found a list at location '{'.'.join(path[:index])}' but did not find a number integer in the targeting, ie failed to convert the next element in the path '{element}' to an integer so can't target the list, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
      if location + 1 > len(currentTier):
        Log(f"Found a list at location '{'.'.join(path[:index])}' that is {len(currentTier)} items long, however '{location}' is not an existing element, hence can't be targeted! Details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
      Log(f'SetNestedValue(): => Moving to nested list property index "{location}"')
      currentTier = currentTier[location]
    elif currentType == str or currentType == int or currentType == bool or currentType == float or currentType == complex:
      if index + 1 >= len(path):
        raise Exception(f"Hit a non-nested type of {currentType} at {index} / {len(path)} after cycling through {', '.join(path[:index])}.\nFull path is {', '.join(path)}.\nTarget Object is:\n{yaml.dump(baseResource)}".encode().decode('unicode-escape'))

def GenerateNestedDict(path:list, value):
  if VerboseSetting > 1:
    Log(f'GenerateNestedDict(): => Generating a nested dict {len(path) - 1} levels deep setting "{path[len(path)-1]}" to "{value}"')
  replicatedObj = {}
  target = replicatedObj
  for index, item in enumerate(path):
    if index + 1 == len(path):
      target[item] = value
      break
    target[item] = {}
    target = target[item]
  return replicatedObj


##########################################
# Logging
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

##########################################
# Argparsing
def ArgParsing():
  parser = argparse.ArgumentParser(description='''Jinny handles complext templating for jinja templates at a large scale and with multiple inputs and with a decent amount of customisation available.

Commonly you'll want to utilse very straight forward features, such as:

=> Templating multiple templates with a single input file:
$ jinny -t template-1.txt template-2.txt -i inputs.yml

=> Templating any number of templates with two input files where base-values.yml provides all the base values and any values in overrides.json acts as an override:
$ jinny -t template.yml -i base-values.yml overrides.json

=> Add even more overrides via environment variables, so your pipelines can completely replace any bad value:
$ JINNY_overridden_value="top-priority" jinny -t template.yml -i base-values.yml overrides.json

=> Pump all your files to a single stdout stream with a separator so different files are clearly marked:
$ jinny -t template-1.yml template-2.yml -i inputs.json -s '---'

=> Dump all your templated files into a directory for capture
$ jinny -t template-1.yml template-2.yml -i inputes.json -d /path/to/directory
$ kubectl diff -f /path/to/directory
$ kubectl apply --server-dry-run -f /path/to/directory

=> Pipe jinny to kubectl for appropriate templating without having to result to Helm
$ jinny -t template-1.yml -i inputs.json | kubectl apply -f -

You can modify jinja's environment settings via the rest of the command line options. Please note that jinny is opinionated and automatically strips line space from templates. You can, of course, turn this off!

''')

  # Core arguments
  parser.add_argument("-v", "--verbose", help="Set output to verbose", action="store_true")
  parser.add_argument("-vvv", "--super-verbose", help="Set output to super verbose where this script will print basically everything", action="store_true")
  parser.add_argument("-i", "--input-values", help="Add one or more file locations that include input values to the templating", action="append", nargs="*")
  parser.add_argument("-t", "--templates", help="Add one or more file locations that contain the templates themselves", action="append", nargs="*", required=True)
  parser.add_argument("-ie", "--ignore-env-vars", help="Tell jinny to ignore any environment variables that begin with JINNY_, defaults to not ignoring these environment variables and setting them at the highest priority", action="store_true")
  parser.add_argument("-ds", "--dict-separator", help="When providing targeting on the CLI or via environment variables, choose a particular separating character for targeting nested elements, defaults to '.'", default=".", type=str)
  parser.add_argument('--version', action='version', version=__version__)

  # Jinja Specific Arguments
  parser.add_argument("--j-block-start", help="Change the characters that indicate the start of a block, default '{%%'", type=str, default="{%")
  parser.add_argument("--j-block-end", help="Change the characters that indicate the end of a block, default '%%}'", type=str, default="%}")
  parser.add_argument("--j-variable-start", help="Change the characters that indicate the start of a variable, default '{{'", type=str, default="{{")
  parser.add_argument("--j-variable-end", help="Change the characters that indicate the end of a variable, default '}}'", type=str, default="}}")
  parser.add_argument("--j-comment-start", help="Change the characters that indicate the start of a comment inside of a template, default '{#'", type=str, default="{#")
  parser.add_argument("--j-comment-end", help="Change the characters that indicate the end of a comment within a template, default '#}'", type=str, default="#}")
  parser.add_argument("--j-trim-blocks", help="Set blocks to trim the newline after a block, this defaults to TRUE in jinny", action="store_false")
  parser.add_argument("--j-lstrip-blocks", help="Set blocks to trim the whitespace before a block, this defaults to TRUE in jinny", action="store_false")
  parser.add_argument("--j-newline-sequence", help="This details the newline in use, defaults to \\n", type=str, default="\n")
  parser.add_argument("--j-keep-trailing-newline", help="Choose whether to trim the newline at the end of a file or not, defaults to TRUE in jinny", action="store_false")

  # Other Arguments
  parser.add_argument("-d", "--dump-to-dir", help="Dump completed templates to a target directory", type=str)
  parser.add_argument("-s", "--stdout-seperator", help="Place a seperator on it's own individual new line between successfully templated template when printing to stdout, eg '---' for yaml", type=str, default='')
  parser.add_argument("-c", "--combine-lists", help="When cascading values across multiple files and encountering two lists with the same key, choose to combine the old list with the new list rather than have the new list replace the old", action="store_false")

  args = parser.parse_args()

  if args.combine_lists:
    CombineLists = True

  if args.verbose:
    VerboseSetting = 1

  if args.super_verbose:
    VerboseSetting = 2

  # jinja2.Environment(bl)
  baseJ2Env = jinja2.Environment(
    block_start_string = args.j_block_start,
    block_end_string = args.j_block_end,
    variable_start_string = args.j_variable_start,
    variable_end_string = args.j_variable_end,
    comment_start_string = args.j_comment_start,
    comment_end_string = args.j_comment_end,
    trim_blocks = args.j_trim_blocks,
    lstrip_blocks = args.j_lstrip_blocks,
    newline_sequence = args.j_newline_sequence,
    keep_trailing_newline = args.j_keep_trailing_newline
  )

  return args

##########################################
# Class
class TemplateHandler():
  def __init__(self, templateName:str="", addToGlobal:bool=False, path:str="", rawString:str=""):
    if not path and not rawString:
      raise Exception(f'TemplateHandler(): Neither a path nor a raw template string was provided, crashing!')
    if path and rawString:
      raise Exception(f'TemplateHandler(): Both a path and a raw string was provided, exiting, wise up!')
    self.path = path
    self.result = None

    if path != "":
      self.name = os.path.abspath(path)
      if not os.path.exists(path):
        Log(f"Failed to read template at path '{path}', cannot load in desired template!", quitWithStatus=1)
      with open(path, "r") as f:
        self.templateData = f.read()
        self.basename = os.path.basename(self.name)
    else:
      if not templateName:
        raise Exception(f'A template name must be provided if passing a raw string template!')
      self.name = "raw provided string"
      self.templateData = rawString
      self.basename = templateName

    try:
      self.loadedTemplate = baseJ2Env.from_string(self.templateData)
    except Exception as e:
      execDetails = sys.exc_info()
      Log(f"Failed to load template at '{path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

    if addToGlobal:
      globalAllTemplatesProcessed[self.name] = self

  def Render(self, values):
    try:
      self.result = self.loadedTemplate.render(values)
    except Exception as e:
      execDetails = sys.exc_info()
      Log(f"Failed to render template at '{self.path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

def ParseValues(*AscendingPriorityInputObjects):
  if len(AscendingPriorityInputObjects) == 0:
    raise Exception(f"ParseValues(): No arguments passed!")
  returningThing = {}
  for thing in AscendingPriorityInputObjects:
    t = type(thing)
    if t == list:
      for listItem in thing:
        returningThing = CombineValues(returningThing, listItem, fullPath)
    else:
      returningThing = CombineValues(returningThing, thing, fullPath)
  return returningThing

def SetJ2Env(**args):
  baseJ2Env = jinja2.Environment(**args)

##########################################
# Direct function

def Main():
  ##########################################
  # Parse CLI Arguments
  args = ArgParsing()
  overallValues = {}
  stdoutDump = []
  ##########################################
  # Template Handling
  for tmpl in args.templates:
    for tmplChild in tmpl:
      fullPath = os.path.abspath(tmplChild)
      TemplateHandler(path=fullPath, addToGlobal=True)

  ##########################################
  # Variable Handling
  for inputsPath in args.input_values:
    for inputsPathChild in inputsPath:
      fullPath = os.path.abspath(inputsPathChild)
      if not os.path.exists(inputsPathChild):
        Log(f"Could not open inputs file at path '{inputsPathChild}'", quitWithStatus=1)
    
      matchedType = ""
      finalObj = None
      with open(inputsPathChild) as f:
        fileData = f.read()

      try:
        ymlObj = yaml.load(fileData, Loader=yaml.FullLoader)
        finalObj = ymlObj
        matchedType = "yaml"
      except Exception as e:
        pass

      if matchedType == "":
        try:
          jsonObj = json.loads(fileData)
          finalObj = jsonObj
          matchedType = "json"
        except Exception as e:
          pass

      if matchedType == "":
        Log(f"Could not load inputs file '{inputsPathChild}' as either a json or a yaml file, please inspect!", quitWithStatus=1)

      overallValues = CombineValues(overallValues, finalObj, fullPath)

  if not args.ignore_env_vars:
    foundVars = {}
    for e in os.environ.keys():
      if e.startswith("JINNY_") and len(e) > 6:
        foundVars[e[6:]] = os.environ[e]

    for path, val in enumerate(foundVars):
      nestedVal = path.split(args.dict_separator)
      SetNestedValue(baseResource=overallValues, path=nestedVal, value=val)

  ##########################################
  # Templating
  for ind, tmpl in enumerate(globalAllTemplatesProcessed):
    globalAllTemplatesProcessed[tmpl].Render(overallValues)

    if args.dump_to_dir:
      dest = args.dump_to_dir + f'/{ind}-{globalAllTemplatesProcessed[tmpl].basename}'
      with open(dest, "w+") as f:
        f.write(globalAllTemplatesProcessed[tmpl].result)
    else:
      stdoutDump.append(globalAllTemplatesProcessed[tmpl].result)

  if not args.dump_to_dir:
    print(f'\n{args.stdout_seperator}\n'.join(stdoutDump))

if __name__ == "__main__":
  Main()