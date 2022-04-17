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

import jinny_logging
import jinny_merging

##########################################
# Variables

globalAllTemplatesProcessed = {}
baseJ2Env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)

##########################################
# Argparsing
def ArgParsing():
  parser = argparse.ArgumentParser(description="Handles templating for jinja templates at a large scale and with multiple inputs")

  # Core arguments
  parser.add_argument("-v", "--verbose", help="Set output to verbose", action="store_true")
  parser.add_argument("-vvv", "--super-verbose", help="Set output to super verbose where this script will print basically everything", action="store_true")
  parser.add_argument("-i", "--input-values", help="Add one or more file locations that include input values to the templating", action="append", nargs="*")
  parser.add_argument("-t", "--templates", help="Add one or more file locations that contain the templates themselves", action="append", nargs="*", required=True)
  parser.add_argument("-ie", "--ignore-env-vars", help="Tell jinny to ignore any environment variables that begin with JINNY_, defaults to not ignoring these environment variables and setting them at the highest priority", action="store_true")
  parser.add_argument("-ds", "--dict-separator", help="When providing targeting on the CLI or via environment variables, choose a particular separating character for targeting nested elements, defaults to '.'", default=".", type=str)

  # Jinja Specific Arguments
  parser.add_argument("--j-block-start", help="Change the characters that indicate the start of a block, default '{%'", type=str, default="{%")
  parser.add_argument("--j-block-end", help="Change the characters that indicate the end of a block, default '%}'", type=str, default="%}")
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

  print(sys.argv)
  args = parser.parse_args()

  if args.combine_lists:
    jinny_merging.CombineLists = True

  if args.verbose:
    jinny_merging.VerboseSetting = 1
    jinny_merging.LoggingFunction = jinny_logging.Log

  if args.super_verbose:
    jinny_merging.VerboseSetting = 2
    jinny_merging.LoggingFunction = jinny_logging.Log

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
        jinny_logging.Log(f"Failed to read template at path '{path}', cannot load in desired template!", quitWithStatus=1)
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
      jinny_logging.Log(f"Failed to load template at '{path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

    if addToGlobal:
      globalAllTemplatesProcessed[self.name] = self

  def Render(self, values):
    try:
      self.result = self.loadedTemplate.render(values)
    except Exception as e:
      execDetails = sys.exc_info()
      jinny_logging.Log(f"Failed to render template at '{self.path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}", quitWithStatus=1)

def ParseValues(*AscendingPriorityInputObjects):
  if len(AscendingPriorityInputObjects) == 0:
    raise Exception(f"ParseValues(): No arguments passed!")
  returningThing = {}
  for thing in AscendingPriorityInputObjects:
    t = type(thing)
    if t == list:
      for listItem in thing:
        returningThing = jinny_merging.CombineValues(returningThing, listItem, fullPath)
    else:
      returningThing = jinny_merging.CombineValues(returningThing, thing, fullPath)
  return returningThing

def SetJ2Env(**args):
  baseJ2Env = jinja2.Environment(**args)

##########################################
# Direct function
if __name__ == "__main__":
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
        jinny_logging.Log(f"Could not open inputs file at path '{inputsPathChild}'", quitWithStatus=1)
    
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
        jinny_logging.Log(f"Could not load inputs file '{inputsPathChild}' as either a json or a yaml file, please inspect!", quitWithStatus=1)

      overallValues = jinny_merging.CombineValues(overallValues, finalObj, fullPath)

  if not args.ignore_env_vars:
    foundVars = {}
    for e in os.environ.keys():
      if e.startswith("JINNY_") and len(e) > 6:
        foundVars[e[6:]] = os.environ[e]

    for path, val in enumerate(foundVars):
      nestedVal = path.split(args.dict_separator)
      jinny_merging.SetNestedValue(baseResource=overallValues, path=nestedVal, value=val)

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
