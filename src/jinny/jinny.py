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

import jinny_logging
import jinny_merging

##########################################
# Variables

globalAllTemplatesProcessed = {}
baseJ2Env = jinja2.Environment()

##########################################
# Argparsing
def ArgParsing():
  parser = argparse.ArgumentParser(description="Handles templating for jinja templates at a large scale and with multiple inputs")

  # Core arguments
  parser.add_argument("-v", "--verbose", help="Set output to verbose", action="store_true")
  parser.add_argument("-vvv", "--super-verbose", help="Set output to super verbose where this script will print basically everything", action="store_true")
  parser.add_argument("-i", "--input-values", help="Add one or more file locations that include input values to the templating", action="append", nargs="*")
  parser.add_argument("-t", "--templates", help="Add one or more file locations that contain the templates themselves", action="append", nargs="*")
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
  parser.add_argument("-d", "--dump-to-dir", help="Dump completed templates to a target directory", nargs="1", type=str)
  parser.add_argument("-s", "--stdout-seperator", help="Place a seperator on it's own individual new line between successfully templated template when printing to stdout, eg '---' for yaml", nargs="1", type=str, default='')
  parser.add_argument("-c", "--combine-lists", help="When cascading values across multiple files and encountering two lists with the same key, choose to combine the old list with the new list rather than have the new list replace the old", action="store_false")

  args = parser.parse_args()

  if args.c:
    jinny_merging.CombineLists = True

  if args.v:
    jinny_merging.VerboseSetting = 1
    jinny_merging.LoggingFunction = jinny_logging.Log

  if args.vvv:
    jinny_merging.VerboseSetting = 2
    jinny_merging.LoggingFunction = jinny_logging.Log

  baseJ2Env = jinja2.Environment(
    block_start = args.j-block-start,
    block_end = args.j-block-end,
    variable_start = args.j-variable-start,
    variable_end = args.j-variable-end,
    comment_start = args.j-comment-start,
    comment_end = args.j-comment-end,
    trim_blocks = args.j-trim-blocks,
    lstrip_blocks = args.j-lstrip-blocks,
    newline_sequence = args.j-newline-sequence,
    keep_trailing_newline = args.j-keep-trailing-newline
  )

  return args

##########################################
# Class
class TemplateHandler():
  def __init__(self, path:str="", rawString:str="", templateName:str, addToGlobal=False):
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
      self.loadedTemplate = j2Env.from_string(self.templateData)
    except Exception as e:
      execDetails = sys.exc_info()
      jinny_logging.Log(f"Failed to load template at '{path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)

    if addToGlobal:
      globalAllTemplates[self.name] = self

  def Render(self, values):
    try:
      self.result = self.loadedTemplate.render(values)
    except Exception as e:
      execDetails = sys.exc_info()
      jinny_logging.Log(f"Failed to render template at '{self.path}' with an exception from Jinja, details:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{execDetails[2]}", quitWithStatus=1)

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

def SetJ2Env(args**):
  baseJ2Env = jinja2.Environment(args**)


if __name__ == __main__:
  ##########################################
  # Parse CLI Arguments
  args = ArgParsing()
  overallValues = {}
  ##########################################
  # Template Handling
  for tmpl in args.t:
    fullPath = os.path.abspath(tmpl)
    TemplateHandler(path=fullPath, addToGlobal=True)

  ##########################################
  # Variable Handling
  for inputsPath in args.i:
    fullPath = os.path.abspath(inputsPath)
    if not os.path.exists(inputsPath):
      jinny_logging.Log(f"Could not open inputs file at path '{inputsPath}'", quitWithStatus=1)
    
    matchedType = ""
    finalObj = None
    with open(inputsPath) as f:
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
      jinny_logging.Log(f"Could not load inputs file '{inputsPath}' as either a json or a yaml file, please inspect!", quitWithStatus=1)

    overallValues = jinny_merging.CombineValues(overallValues, finalObj, fullPath)

  if not args.ie:
    foundVars = {}
    for e in os.environ.keys():
      if e.startswith("JINNY_") and len(e) > 6:
        foundVars[e[6:]] = os.environ[e]

    for path, val in enumerate(foundVars):
      nestedVal = path.split(args.ds)
      jinny_merging.SetNestedValue(baseResource=overallValues, path=nestedVal, value=val)

  ##########################################
  # Templating
  for ind, tmpl in enumerate(globalAllTemplatesProcessed):
    tmpl.Render(overallValues)

    if args.d:
      dest = args.d + f'/{ind}-{tmpl.basename}'
      with open(dest, "w+") as f:
        f.write(tmpl.result)
    else:
      stdoutDump.append(tmpl.result)

  if not args.d:
    print(f'\n{args.s}\n'.join(stdoutDump))
