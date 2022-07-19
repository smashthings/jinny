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
import pathlib

baseDir = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(f'{baseDir}/version'):
  print(f"Jinny's version file doesn't exist, expected to find it at {basedir}/version. Not a good sign, might be best to reinstall jinny!")
  __version__ = "mystery.version"

with open(f'{baseDir}/version') as f:
  __version__ = f.read().strip("\n")

##########################################
# Variables

class LoggingSettings():
  def __init__(self, location:str="/dev/stdout", colour:bool=True, verbosity:int=0):
    self.location = location
    self.colour = colour
    self.verbosity = verbosity

    self.beginChar = "\033[92m" if colour else ''
    self.badChar = "\033[91m" if colour else ''
    self.warnChar = "\033[93m" if colour else ''
    self.endChar = "\033[0m" if colour else ''


globalAllTemplatesProcessed = {}
baseJ2Env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
CombineLists = False
args = None

CurrentLoggingSettings = LoggingSettings()

##########################################
# Machinery
def CombineValues(originalVals, newVals, sourceName:str):
  originalType = type(originalVals)
  newType = type(newVals)
  if CurrentLoggingSettings.verbosity > 0:
    Log(f'CombineValues(): handling {sourceName}, original item = {originalType!s}, new item = {newType!s}')

  # Easy wins
  if originalType == list and newType == list:
    if CurrentLoggingSettings.verbosity > 0:
      Log(f'CombineValues(): found two lists, {"combining and returning" if CombineLists else "replacing old list with new one"}')
    return originalVals + newVals if CombineLists else newVals

  if originalType == None:
    if CurrentLoggingSettings.verbosity > 0:
      Log(f'CombineValues(): original item is None, replacing with new item')
    return newVals
  
  if newType == None:
    if CurrentLoggingSettings.verbosity > 0:
      Log(f'CombineValues(): new item is None, returning None')
    return None

  # More Common
  if originalType == dict and newType == dict:
    if CurrentLoggingSettings.verbosity > 1:
      Log(f'CombineValues(): Handling a dict merge')
    workingVals = originalVals.copy()
    origKeys = originalVals.keys()
    for eleKey, eleVal in newVals.items():
      if eleKey not in origKeys:
        if CurrentLoggingSettings.verbosity > 1:
          Log(f'CombineValues(): => Adding new key "{eleKey}"')
        workingVals[eleKey] = eleVal
        continue

      newType = type(eleVal)
      oldType = type(originalVals[eleKey])
      if newType == str or newType == int or newType == bool or newType == float or newType == complex:
        if CurrentLoggingSettings.verbosity > 1:
          Log(f'CombineValues(): => Updated value for "{eleKey}"')
        workingVals[eleKey] = eleVal
        continue
      if oldType == list and newType == list:
        if originalVals[eleKey] == newVals[eleKey]:
          if CurrentLoggingSettings.verbosity > 1:
            Log(f'CombineValues(): => Key "{eleKey}" is the same list in both old and new, continuing')
        else:
          if CurrentLoggingSettings.verbosity > 1:
            Log(f'CombineValues(): => Key "{eleKey}" is an altered list, {"combining and continuing" if CombineLists else "replacing old list with new one"}')
          workingVals[eleKey] = originalVals[eleKey] + newVals[eleKey] if CombineLists else newVals[eleKey]
        continue

      if oldType == dict and newType != dict:
        if CurrentLoggingSettings.verbosity > 1:
          Log(f'CombineValues(): => Key "{eleKey}" was a dict but updated to be a {newType!s}, replacing')
        workingVals[eleKey] = newVals[eleKey]
        continue

      if newType == dict and newType == dict:
        if CurrentLoggingSettings.verbosity > 1:
          Log(f'CombineValues(): => Key "{eleKey}" is a dict updated with another dict, recursively calling CombineValues to handle')
        res = CombineValues(originalVals[eleKey], newVals[eleKey], sourceName)
        workingVals[eleKey] = res

    return workingVals

def SetNestedValue(baseResource, path:list, value):
  if CurrentLoggingSettings.verbosity > 1:
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
        Log(f"SetNestedValue(): Found a list at location '{'.'.join(path[:index])}' but did not find a number integer in the targeting, ie failed to convert the next element in the path '{element}' to an integer so can't target the list, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
      if location + 1 > len(currentTier):
        Log(f"SetNestedValue(): Found a list at location '{'.'.join(path[:index])}' that is {len(currentTier)} items long, however '{location}' is not an existing element, hence can't be targeted! Details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)
      Log(f'SetNestedValue(): => Moving to nested list property index "{location}"')
      currentTier = currentTier[location]
    elif currentType == str or currentType == int or currentType == bool or currentType == float or currentType == complex:
      if index + 1 >= len(path):
        raise Exception(f"Hit a non-nested type of {currentType} at {index} / {len(path)} after cycling through {', '.join(path[:index])}.\nFull path is {', '.join(path)}.\nTarget Object is:\n{yaml.dump(baseResource)}".encode().decode('unicode-escape'))

def GenerateNestedDict(path:list, value):
  if CurrentLoggingSettings.verbosity > 1:
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


def ParseValuesFile(path:str):
  ext = os.path.basename(path).split(".")
  if len(ext) == 2:
    ext = ext[1]
  else:
    ext = None
  finalObj = None
  with open(path) as f:
    fileData = f.read()

  if ext == "yaml" or ext == "yml":
    try:
      ymlObj = yaml.load(fileData, Loader=yaml.FullLoader)
      return ymlObj
    except Exception as e:
      Log(f"Main(): Inputs file at path '{path}' has a YAML extension naming convention but fails YAML parsing.", AlwaysLog=True)
      if CurrentLoggingSettings.verbosity > 1:
        Log(f'Main(): Full stack trace:\n\n{traceback.format_exc()}', AlwaysLog=True)
      Log(f"Main(): Error:\n{e.problem}\n{e.problem_mark}", AlwaysLog=True)
      Log("Main(): Exiting!", quitWithStatus=2)

  elif ext == "json":
    try:
      jsonObj = json.loads(fileData)
      return jsonObj
    except Exception as e:
      Log(f"Main(): Inputs file at path '{path}' has a JSON extension naming convention but fails JSON parsing.", AlwaysLog=True)
      if CurrentLoggingSettings.verbosity > 1:
        Log(f'Main(): Full stack trace:\n\n{traceback.format_exc()}', AlwaysLog=True)
      Log(f"Main(): Error: {getattr(e, 'msg')} at line {getattr(e, 'lineno')} column {e.colno}", AlwaysLog=True)
      Log("Main(): Exiting!", quitWithStatus=2)

  else:
    try:
      ymlObj = yaml.load(fileData, Loader=yaml.FullLoader)
      return ymlObj
    except Exception as e:
      pass
    
    try:
      jsonObj = json.loads(fileData)
      return jsonObj
    except Exception as e:
      pass
    Log(f"Main(): Could not load inputs file '{path}' as either a JSON or a YAML file, please inspect!", quitWithStatus=1)

##########################################
# Logging
def Log(message, quit:bool=False, quitWithStatus:int=0, AlwaysLog:bool=False):
  if AlwaysLog == False and CurrentLoggingSettings.verbosity == 0 and not quit and quitWithStatus == 0:
    return

  if quit or quitWithStatus > 0:
    if type(message) is dict:
      logToFile(CurrentLoggingSettings.location, f'{CurrentLoggingSettings.badChar}\n*********************\n<{TimeStamp()}>{CurrentLoggingSettings.endChar} - ' + "\n => ".join([k + ": " + str(message[k]) for k in message]))
    else:
      logToFile(CurrentLoggingSettings.location, f'{CurrentLoggingSettings.badChar}\n*********************\n<{TimeStamp()}>{CurrentLoggingSettings.endChar} - {message}')
    exit(max(1, quitWithStatus))

  if type(message) is dict:
    logToFile(CurrentLoggingSettings.location, f'{CurrentLoggingSettings.warnChar if AlwaysLog else CurrentLoggingSettings.beginChar}<{TimeStamp()}>{CurrentLoggingSettings.endChar} - ' + "\n => ".join([k + ": " + str(message[k]) for k in message]))
  else:
    logToFile(CurrentLoggingSettings.location, f'{CurrentLoggingSettings.warnChar if AlwaysLog else CurrentLoggingSettings.beginChar}<{TimeStamp()}>{CurrentLoggingSettings.endChar} - {message}')

##############################################
# Internal Functions
def TimeStamp():
  return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")

def logToFile(path:str, msg:str):
  if path == "/dev/stdout":
    sys.stdout.write(msg + "\n")
  else:
    with open(path, 'a+') as f:
      f.write(msg + "\n")

##########################################
# Argparsing
def ArgParsing():
  global CurrentLoggingSettings
  parser = argparse.ArgumentParser(description=f'''jinny v{__version__} | jinny.scripted.dog
Jinny handles complex templating for jinja templates at a large scale and with multiple inputs and with a decent amount of customisation available.

Commonly you'll want to utilse very straight forward features, such as:

=> Templating multiple templates with a single input file:
$ jinny -t template-1.txt template-2.txt -i inputs.yml

=> Templating any number of templates with two input files where base-values.yml provides all the base values and any values in overrides.json acts as an override:
$ jinny -t template.yml -i base-values.yml overrides.json

=> Add even more overrides via environment variables, so your pipelines can completely replace any bad value:
$ JINNY_overridden_value="top-priority" jinny -t template.yml -i base-values.yml overrides.json

=> Or via CLI:
$ jinny -t template.yml -i base-values.yml -e overridden_value="top-priority" overrides.json

=> Pump all your files to a single stdout stream with a separator so different files are clearly marked:
$ jinny -t template-1.yml template-2.yml -i inputs.json -s='---'

=> Dump all your templated files into a directory for capture
$ jinny -t template-1.yml template-2.yml -i inputes.json -d /path/to/directory
$ kubectl diff -f /path/to/directory
$ kubectl apply --server-dry-run -f /path/to/directory

=> Pipe jinny to kubectl for appropriate templating without having to result to Helm
$ jinny -t template-1.yml -i inputs.json | kubectl apply -f -

You can modify jinja's environment settings via the rest of the command line options. Please note that jinny is opinionated and automatically strips line space from templates. You can, of course, turn this off!

''', formatter_class=argparse.RawTextHelpFormatter)

  # Core arguments
  parser.add_argument("-v", "--verbose", help="Set output to verbose", action="store_true")
  parser.add_argument("-vvv", "--super-verbose", help="Set output to super verbose where this script will print basically everything", action="store_true")
  parser.add_argument("-i", "--inputs", help="Add one or more file locations that include input values to the templating", action="append", nargs="*")
  parser.add_argument("-e", "--explicit", help="Explicitly define a variable that trumps all other variables using a variable=value format. Adding variables like this trumps every other setting for that variable", action="append", nargs="*")
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
  parser.add_argument("-ld", "--log-destination", help="Chose an alternate destination to log to, jinny defaults to stdout but you can provide a file to print output to instead", default="/dev/stdout", type=str)
  parser.add_argument("-nc", "--no-color", "--no-colour", help="Turn off coloured output", action="store_false")

  args = parser.parse_args()

  if args.combine_lists:
    CombineLists = True

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

  # Checking that the directory for the logging location exists
  if args.log_destination != "/dev/stdout" and not os.path.isdir(os.path.dirname(args.log_destination)):
    Log(f"ArgParsing(): The parent directory for the custom log file '{args.log_destination}' either does not exist or is not a directory, please check it!", quitWithStatus=1)

  if type(args.dump_to_dir) == str:
    args.dump_to_dir = args.dump_to_dir.strip('/')
    if not os.path.isdir(os.path.dirname(args.dump_to_dir)):
      Log(f"ArgParsing(): The parent directory for dumping completed templates to '{args.dump_to_dir}' does not exist, please check your arguments!", quitWithStatus=1)

    if os.path.isfile(args.dump_to_dir):
      Log(f"ArgParsing(): The location provided for dumping completed templates to is a file and not a directory '{args.dump_to_dir}', please check your arguments!", quitWithStatus=1)
      
    if not os.path.exists(args.dump_to_dir):
      os.mkdir(args.dump_to_dir)

  vs = 0
  if args.verbose:
    vs = 1
  if args.super_verbose:
    vs = 2
  CurrentLoggingSettings = LoggingSettings(location = args.log_destination, colour = args.no_color, verbosity = vs)

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
        Log(f"TemplateHandler(): Failed to read template at path '{path}', cannot load in desired template!", quitWithStatus=1)
      with open(path, "r") as f:
        self.templateData = f.read()
        self.basename = os.path.basename(self.name)
    else:
      if not templateName:
        raise Exception(f'TemplateHandler(): A template name must be provided if passing a raw string template!')
      self.name = "raw provided string"
      self.templateData = rawString
      self.basename = templateName

    try:
      self.loadedTemplate = baseJ2Env.from_string(self.templateData)
    except Exception as e:
      execDetails = sys.exc_info()
      Log(f"TemplateHandler(): Failed to load template at '{path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

    if addToGlobal:
      globalAllTemplatesProcessed[self.name] = self

  def Render(self, values):
    try:
      self.result = self.loadedTemplate.render(values)
    except Exception as e:
      execDetails = sys.exc_info()
      Log(f"TemplateHandler.Render(): Failed to render template at '{self.path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

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
      tmplFullPath = os.path.abspath(tmplChild)
      if "*" in tmplFullPath:
        Log(f'Main(): Handling template globbing expression {tmplFullPath}...')
        s = tmplFullPath.find('*')
        for globbedTemplatePath in pathlib.Path(tmplFullPath[:s]).glob(tmplFullPath[s:]):
          if CurrentLoggingSettings.verbosity > 1:
            Log(f'Main(): => {globbedTemplatePath}...')
          if globbedTemplatePath.is_file():
            TemplateHandler(path=globbedTemplatePath, addToGlobal=True)
      else:
        TemplateHandler(path=tmplFullPath, addToGlobal=True)

  ##########################################
  # Variable Handling
  for inputsPath in args.inputs:
    for inputsPathChild in inputsPath:
      inputFullPath = os.path.abspath(inputsPathChild)
      if "*" in inputFullPath:
        s = inputFullPath.find('*')
        Log(f'Main(): Handling inputs globbing expression {inputFullPath}...')
        
        for globbedInputPath in pathlib.Path(inputFullPath[:s]).glob(inputFullPath[s:]):
          if CurrentLoggingSettings.verbosity > 1:
            Log(f'Main(): => {globbedInputPath}...')
          overallValues = CombineValues(overallValues, ParseValuesFile(globbedInputPath), globbedInputPath)
        continue

      if not os.path.exists(inputFullPath):
        Log(f"Main(): Could not open inputs file at path '{inputFullPath}'", quitWithStatus=1)

      if os.stat(inputFullPath).st_size == 0:
        continue

      overallValues = CombineValues(overallValues, ParseValuesFile(inputFullPath), inputFullPath)

  if not args.ignore_env_vars:
    foundVars = {}
    for e in os.environ.keys():
      if e.startswith("JINNY_") and len(e) > 6:
        foundVars[e[6:]] = os.environ[e]

    for path, val in enumerate(foundVars):
      nestedVal = path.split(args.dict_separator)
      SetNestedValue(baseResource=overallValues, path=nestedVal, value=val)

  if args.explicit:
    foundExplicitVars = {}
    for explicitValList in args.explicit:
      for explicitVal in explicitValList:

        splits = explicitVal.split("=")
        foundExplicitVars[splits[0]] = "=".join(splits[1:])

    for path in foundExplicitVars:
      nestedVal = path.split(args.dict_separator)
      SetNestedValue(baseResource=overallValues, path=nestedVal, value=foundExplicitVars[path])

  ##########################################
  # Templating
  for ind, tmpl in enumerate(globalAllTemplatesProcessed):
    globalAllTemplatesProcessed[tmpl].Render(overallValues)

    if globalAllTemplatesProcessed[tmpl].result == "":
      continue

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