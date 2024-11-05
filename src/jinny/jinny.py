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
import inspect

baseDir = os.path.dirname(os.path.abspath(__file__))
if __name__ == '__main__':
  from imports import jinny_unsafe
  from imports import filter_extensions
  from imports import global_extensions
else:
  sys.path.insert(0, baseDir)
  from imports import jinny_unsafe
  from imports import filter_extensions
  from imports import global_extensions
  sys.path.pop(0)

if not os.path.exists(f'{baseDir}/version'):
  print(f"Jinny's version file doesn't exist, expected to find it at {baseDir}/version. Not a good sign, might be best to reinstall jinny!")
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
workingValsPointer = None
HtmlErrorTemplate = None
HtmlErrorTemplateExitNumber = 0

CurrentLoggingSettings = LoggingSettings()

def ActivateJinnyUnsafe():
  jinny_unsafe.Activate()

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
  ext = ext[-1]
  Log(f'ParseValuesFile(): Received path {path} with extension {ext}')
  if not os.path.isfile(path):
    Log(f"ParseValuesFile(): Inputs file at path '{path}' doesn't exist.", AlwaysLog=True)
    Log("ParseValuesFile(): Exiting!", quitWithStatus=2)

  if ext == "yaml" or ext == "yml":
    try:
      with open(path) as f:
        fileData = f.read()
      ymlObj = yaml.load(fileData, Loader=yaml.FullLoader)
      return ymlObj
    except Exception as e:
      Log(f"ParseValuesFile(): Inputs file at path '{path}' has a YAML extension naming convention but fails YAML parsing.", AlwaysLog=True)
      if CurrentLoggingSettings.verbosity > 1:
        Log(f'ParseValuesFile(): Full stack trace:\n\n{traceback.format_exc()}', AlwaysLog=True)
      Log(f"ParseValuesFile(): Error:\n{e.problem}\n{e.problem_mark}", AlwaysLog=True)
      Log("ParseValuesFile(): Exiting!", quitWithStatus=2)

  elif ext == "json":
    try:
      with open(path) as f:
        fileData = f.read()
      jsonObj = json.loads(fileData)
      return jsonObj
    except Exception as e:
      Log(f"ParseValuesFile(): Inputs file at path '{path}' has a JSON extension naming convention but fails JSON parsing.", AlwaysLog=True)
      if CurrentLoggingSettings.verbosity > 1:
        Log(f'ParseValuesFile(): Full stack trace:\n\n{traceback.format_exc()}', AlwaysLog=True)
      Log(f"ParseValuesFile(): Error: {getattr(e, 'msg')} at line {getattr(e, 'lineno')} column {e.colno}", AlwaysLog=True)
      Log("ParseValuesFile(): Exiting!", quitWithStatus=2)

  elif ext == "env":
    returningVals = {}
    lastKey = None
    with open(path) as f:
      for ln, l in enumerate(f.readlines()):
        st = l.strip()
        if not st or st[0] == '#':
          continue
        s = l.split('=')
        le = len(s)
        if le >= 2:
          returningVals[s[0]] = '='.join(s[1:]).rstrip('\n')
          lastKey = s[0]
          continue
        elif le == 1 and lastKey != None:
          # Appending this value onto the end of the last value with a new line intermediary
          returningVals[lastKey] = returningVals[lastKey] + '\n' + s[0].rstrip('\n')
          continue
        elif le == 1 and lastKey == None:
          Log(f"ParseValuesFile(): Error: Could not understand environment file at line {ln}. There hasn't been a previous key parsed yet this line does not have a key=value format. Not sure what to do. If this is a comment then prepend the line with #", AlwaysLog=True)
          Log("ParseValuesFile(): Exiting!", quitWithStatus=2)
        else:
          Log(f"ParseValuesFile(): Error: Could not understand environment file at line {ln}. This line did not parse as a key=value format. Not sure what to do.", AlwaysLog=True)
          Log("ParseValuesFile(): Exiting!", quitWithStatus=2)
    return returningVals

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
    Log(f"ParseValuesFile(): Could not load inputs file '{path}' as either a JSON or a YAML file, please inspect!", quitWithStatus=1)

def LoadCustomFilters():
  global baseJ2Env
  for f in inspect.getmembers(filter_extensions, inspect.isfunction):
    baseJ2Env.filters.update({f[0]: f[1]})
  for f in inspect.getmembers(global_extensions, inspect.isfunction):
    baseJ2Env.globals.update({f[0]: f[1]})
  for f in jinny_unsafe.UnsafeFiltersMap.keys():
    baseJ2Env.filters.update({f: jinny_unsafe.UnsafeFiltersMap[f]})
  for f in jinny_unsafe.UnsafeGlobalMap.keys():
    baseJ2Env.globals.update({f: jinny_unsafe.UnsafeGlobalMap[f]})
  baseJ2Env.filters.update({
    'nested_template': NestedTemplate
  })

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

def NestedTemplate(filename):
  if os.path.exists(filename):
    dest = filename
  elif os.path.exists(os.path.abspath(filename)):
    dest = os.path.abspath(filename)
  else:
    raise Exception(f"jinny.filter_extenions.nested_template(): The file at path {filename} does not exist!")

  Log(f'NestedTemplate(): {dest}')
  nt = TemplateHandler(
    templateName=f'(Nested) - {os.path.basename(dest)}',
    addToGlobal=False,
    nested=True,
    path=dest,
  )
  try:
    res = nt.Render(workingValsPointer)
    return nt.Result()
  except Exception as e:
    print(f"jinny.filter_extenions.nested_template(): Failed to read and template from file {filename} with exception")
    traceback.print_exception(e)
    raise


##########################################
# Argparsing
def ArgParsing():
  global CurrentLoggingSettings
  global baseJ2Env
  global args
  global CombineLists
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
  parser.add_argument("-vvv", "--super-verbose", help="Set output to super verbose where this script will print basically everything, INCLUDING POTENTIALLY SENSITIVE THINGS!", action="store_true")
  parser.add_argument("-i", "--inputs", help="Add one or more file locations that include input values to the templating", action="append", nargs="*")
  parser.add_argument("-e", "--explicit", help="Explicitly define a variable that trumps all other variables using a variable=value format. Adding variables like this trumps every other setting for that variable", action="append", nargs="*")
  parser.add_argument("-t", "--templates", help="Add one or more file locations that contain the templates themselves", action="append", nargs="*", required=True)
  parser.add_argument("-ie", "--ignore-env-vars", help="Tell jinny to ignore any environment variables that begin with JINNY_, defaults to not ignoring these environment variables and setting them at the highest priority", action="store_true")
  parser.add_argument("-ds", "--dict-separator", help="When providing targeting on the CLI or via environment variables, choose a particular separating character for targeting nested elements, defaults to '.'", default=".", type=str)
  parser.add_argument('--version', action='version', version=__version__)

  # Other Arguments
  parser.add_argument("-d", "--dump-to-dir", help="Dump completed templates to a target directory", type=str)
  parser.add_argument("-di", "--dump-to-dir-no-index", help="Dump completed templates to a target directory without index separation, meaning that templates with the same name can overwrite prior templates", type=str)
  parser.add_argument("-s", "--stdout-seperator", help="Place a seperator on it's own individual new line between successfully templated template when printing to stdout, eg '---' for yaml", type=str, default='')
  parser.add_argument("-c", "--combine-lists", help="When cascading values across multiple files and encountering two lists with the same key, choose to combine the old list with the new list rather than have the new list replace the old", action="store_false")
  parser.add_argument("-ld", "--log-destination", help="Chose an alternate destination to log to, jinny defaults to stdout but you can provide a file to print output to instead", default="/dev/stdout", type=str)
  parser.add_argument("-nc", "--no-color", "--no-colour", help="Turn off coloured output", action="store_false")
  parser.add_argument("-he", "--html-error", help="When encountering an error on the current template render a HTML error page with details on the error as well as log the error. This allows for templating errors to be captured by live browser reloads. Seriously, don't use this in prod", action="store_true")
  parser.add_argument("-u", "--unsafe", dest='unsafe', help="Load unsafe filters and extensions, check the documentation", action="store_true")

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

  args = parser.parse_args()

  if args.combine_lists:
    CombineLists = True

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

  if type(args.dump_to_dir) == str or type(args.dump_to_dir_no_index) == str:
    tarDump = "dump_to_dir" if type(args.dump_to_dir) == str else "dump_to_dir_no_index"
    args.__setattr__(tarDump, getattr(args, tarDump).rstrip('/'))
    if not os.path.isdir(getattr(args, tarDump)):
      Log(f"ArgParsing(): The parent directory for dumping completed templates to '{getattr(args, tarDump)}' does not exist, please check your arguments!", quitWithStatus=1)

    if os.path.isfile(getattr(args, tarDump)):
      Log(f"ArgParsing(): The location provided for dumping completed templates to is a file and not a directory '{getattr(args, tarDump)}', please check your arguments!", quitWithStatus=1)

  vs = 0
  if args.verbose:
    vs = 1
  if args.super_verbose:
    vs = 2
  CurrentLoggingSettings = LoggingSettings(location = args.log_destination, colour = args.no_color, verbosity = vs)

  import imports.jinny_unsafe as jinny_unsafe
  if args.unsafe:
    ActivateJinnyUnsafe()

  return args

##########################################
# Class
class TemplateHandler():
  def __init__(self, templateName:str="", addToGlobal:bool=False, path:str="", rawString:str="", nested:bool=False):
    Log(f'TemplateHandler(): Handling template at path {path}')
    if not path and not rawString:
      raise Exception(f'TemplateHandler(): Neither a path nor a raw template string was provided, crashing!')
    if path and rawString:
      raise Exception(f'TemplateHandler(): Both a path and a raw string was provided, exiting, wise up!')
    self.path = path
    self.result = None
    self.nested = nested

    if path != "":
      self.name = os.path.abspath(path)
      if not os.path.exists(path):
        Log(f"TemplateHandler(): Failed to read {'nested template' if self.nested else 'template' } at path '{path}', cannot load in desired template!", quitWithStatus=1)
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
      Log(f"TemplateHandler(): Failed to load {'nested template' if self.nested  else 'template' } at '{path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

    self.extensions = {
      "path": {
        "cwd": os.getcwd().rstrip("/") + "/",
        "jinny": baseDir.rstrip("/") + "/",
        "template": os.path.abspath(path) if path else "",
        "templatedir": os.path.dirname(os.path.abspath(path)).rstrip("/") + "/" if path else "",
        "home": os.path.expanduser('~').rstrip("/") + "/"
      }
    }

    if addToGlobal:
      globalAllTemplatesProcessed[self.name] = self

  def Render(self, values):
    Log(f"TemplateHandler.Render({self.name}): Started render")
    self.loadedTemplate.environment.globals["path"] = self.extensions["path"]
    try:
      if not self.nested:
        global workingValsPointer
        workingValsPointer = values
      self.result = self.loadedTemplate.render(values)
      if not self.nested:
        workingValsPointer = None
    except Exception as e:
      execDetails = sys.exc_info()
      if args and args.html_error:
        Log(f"TemplateHandler.Render(): Failed to render {'nested template' if self.nested  else 'template' } at '{self.path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", AlwaysLog=True)
        Log(f'TemplateHandler.Render() Setting template to error page...', AlwaysLog=True)
        HtmlErrorTemplate.Render({
          'nested': self.nested,
          'template_path': self.path,
          'error_type': 'jinja2.exceptions.' + execDetails[0].__name__,
          'error_value': str(execDetails[1]),
          'lines': traceback.format_exc().splitlines()
        })
        self.result = HtmlErrorTemplate.Result()
        global HtmlErrorTemplateExitNumber
        HtmlErrorTemplateExitNumber += 1
      else:
        Log(f"TemplateHandler.Render(): Failed to render {'nested template' if self.nested  else 'template' } at '{self.path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

  def Result(self):
    return self.result if self.result else None

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

##########################################
# Direct function

def Main():
  ##########################################
  # Parse CLI Arguments
  args = ArgParsing()
  LoadCustomFilters()
  overallValues = {}
  stdoutDump = []

  if args.html_error:
    if not os.path.exists(f'{baseDir}/error.html'):
      global HtmlErrorTemplate
      HtmlErrorTemplate = TemplateHandler(path=f'{baseDir}/error.html', addToGlobal=False)
    else:
      Log(f'Main(): Did not find error HTML template at {baseDir}/error.html for option --html-error! This option will be skipped and errors crashed as usual')
      args.html_error = False

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
  if args.inputs:
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

    # Bugfix from using enumerate to items contributed by @cazgp 
    for path, val in foundVars.items():
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
  if args.super_verbose:
    Log("Main(): Calculated values:")
    print(json.dumps(overallValues, indent=2))
  for ind, tmpl in enumerate(globalAllTemplatesProcessed):
    globalAllTemplatesProcessed[tmpl].Render(overallValues)

    if globalAllTemplatesProcessed[tmpl].result == "":
      continue

    if args.dump_to_dir or args.dump_to_dir_no_index:
      tarDump = "dump_to_dir" if type(args.dump_to_dir) == str else "dump_to_dir_no_index"
      dest = getattr(args, tarDump) + f'/{str(ind) + "-" if args.dump_to_dir else "" }{globalAllTemplatesProcessed[tmpl].basename}'
      with open(dest, "w+") as f:
        f.write(globalAllTemplatesProcessed[tmpl].result)
    else:
      stdoutDump.append(globalAllTemplatesProcessed[tmpl].result)

  if not args.dump_to_dir and not args.dump_to_dir_no_index:
    print(f'\n{args.stdout_seperator}\n'.join(stdoutDump))

  if args.html_error:
    if HtmlErrorTemplateExitNumber > 0:
      Log(f"Main(): Templated {HtmlErrorTemplateExitNumber} failed templates!", quitWithStatus=1)
    else:
      Log(f"Main(): All templates completed without errors!")

if __name__ == "__main__":
  Main()