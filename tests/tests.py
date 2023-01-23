#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/jinny')))

import yaml
import json
import traceback
import subprocess
import pytest
import datetime

import jinny
import inspect

jinny.VerboseSetting = 2
jinny.LoadCustomFilters()

##########################################
# Paths
currentDir = os.path.abspath(os.path.dirname(__file__))
jinnyDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/jinny'))
assetsDir = f"{currentDir}/test_assets"

##########################################
# Helpers
def RunCmd(listOfCommands:list):
  print(f'Running command: {" ".join(listOfCommands)}')
  cmd = subprocess.run(list(listOfCommands), shell=False, cwd=currentDir, capture_output=True)
  return (cmd.returncode, cmd.stdout.decode('utf-8'), cmd.stderr.decode('utf-8'))

##########################################
# Merge Tests
def test_combine_lists():
  jinny.CombineLists = True
  res = jinny.CombineValues(["one", "two"], ["ay", "be"], 'test_combine_lists')
  assert res == ["one", "two", "ay", "be"]

def test_replace_lists():
  jinny.CombineLists = False
  res = jinny.CombineValues(["one", "two"], ["ay", "be"], 'test_replace_lists')
  assert res == ["ay", "be"]

def test_merging_dicts():
  res = jinny.CombineValues({
    "first": True
  }, {
    "second": "please"
  }, 'test_merging_dicts')
  assert res["first"] == True
  assert res["second"] == "please"

def test_nested_dicts():
  res = jinny.CombineValues({
    "first": True,
    "nest_one": {
      "mushrooms": 4,
      "fungus": True,
      "toppings": [
        "salamanders",
        3,
        False
      ],
      "nest_two": {
        "wizards": True,
        "about": 10,
        "such_as": [
          "derek",
          8,
          False
        ]
      }
    }
  }, {
    "first": False,
    "nest_one": {
      "mushrooms": 4,
      "acid_trip": False,
      "toppings": [
        "salamanders",
        3,
        False,
      ],
      "another_list": [
        "oh_noes"
      ],
      "nest_two": None
    }
  }, 'test_nested_dicts')
  assert res["first"] == False
  assert res["nest_one"]["mushrooms"] == 4
  assert res["nest_one"]["fungus"] == True
  assert res["nest_one"]["acid_trip"] == False
  assert type(res["nest_one"]["another_list"]) == list
  assert len(res["nest_one"]["another_list"]) == 1
  assert type(res["nest_one"]["toppings"]) == list
  assert res["nest_one"]["toppings"] == ["salamanders", 3, False]
  assert res["nest_one"]["nest_two"] == None

def test_mega_nest():
  res = jinny.CombineValues({
    "nest_one": {
      "nest_two": {
        "nest_three": {
          "nest_four": {
            "nest_five": {
              "b": True,
              "n": 0,
              "s": "stringy"
            }
          }
        }
      }
    }
  }, {
    "secondary_nest_one":{
      "secondary_nest_two": {
        "secondary_nest_three": {
          "secondary_nest_four": {
            "secondary_nest_five": True
          }
        }
      }
    },
    "nest_one": {
      "nest_two": {
        "nest_three": {
          "nest_four": {
            "nest_five": {
              "b": True,
              "n": 0,
              "s": "stringy",
              "nest_six": {
                "b6": False,
                "n6": 1,
                "s6": "stringy6",
              }
            }
          }
        }
      }
    }
  }, 'test_nested_dicts')
  assert res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["b"] == True
  assert res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["s"] == "stringy"
  assert res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["n"] == 0
  assert type(res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["nest_six"]) == dict
  assert res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["nest_six"]["b6"] == False
  assert res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["nest_six"]["n6"] == 1
  assert res["nest_one"]["nest_two"]["nest_three"]["nest_four"]["nest_five"]["nest_six"]["s6"] == "stringy6"
  assert res["secondary_nest_one"]["secondary_nest_two"]["secondary_nest_three"]["secondary_nest_four"]["secondary_nest_five"] == True


def test_targeting_nested_resources():
  origResource = {
    "dicts": [
      {
        "thing": "this",
        "nest_one": {
          "mushrooms": True
        }
      },
      {
        "toppings": [
          {
            "dict_num": 3,
            "dict_dict": {
              "dict_dict_dict": True
            }
          }
        ]
      }
    ]
  }
  jinny.SetNestedValue(origResource, ["dicts", "0", "nest_one", "mushrooms"], False)
  jinny.SetNestedValue(origResource, ["dicts", "1", "added_resource"], 4)
  jinny.SetNestedValue(origResource, ["dicts", "1", "toppings", "0", "dict_dict", "other"], False)
  assert origResource["dicts"][0]['nest_one']['mushrooms'] == False
  assert origResource["dicts"][1]['added_resource'] == 4
  assert origResource["dicts"][1]['toppings'][0]['dict_dict']['other'] == False

def test_generated_nest():
  res = jinny.GenerateNestedDict(["nest_one", "nest_two", "nest_three", "key"], True)
  assert res["nest_one"]["nest_two"]["nest_three"]["key"] == True


##########################################
# Templating
def test_provided_template_with_basic_inputs():
  templFile = f"{assetsDir}/sample_template.yml"
  with open(templFile) as f:
    templData = f.read()
  tmplClass = jinny.TemplateHandler(templateName="test_provided_template_with_basic_inputs", rawString=templData)
  vals = {
    "release_name": "testing",
    "namespace": "default",
    "listening_port": 5000,
    "nodeport": 32010,
    "ports": {
      "web": 80,
      "app-port": 5000
    },
    "common_labels": {
      "app": "testing-app",
      "version": "latest"
    }
  }

  tmplClass.Render(vals)
  res = tmplClass.result
  res2 = tmplClass.Result()

  try:
    assertingYaml = yaml.load_all(res, Loader=yaml.FullLoader)
    assertingYamlAgain = yaml.load_all(res2, Loader=yaml.FullLoader)
  except Exception as e:
    execDetails = sys.exc_info()
    print(f"Failed to output to yaml with exception:\nType:{execDetails[0]}\nValue:{execDetails[1]}\nTrace:\n{traceback.format_exc()}")
    print(res)
    assert False
  assert True

##########################################
# CLI
def test_cli_with_values():
  templFile = f"{assetsDir}/sample_template.yml"
  valuesFile = f'{assetsDir}/sample_values.yml'
  status, stdout, stderr = RunCmd([
    "python3",
    f'{jinnyDir}/jinny.py',
    "-i",
    valuesFile,
    "-t",
    templFile
    ])
  
  print(stdout)
  print(stderr)
  print(status)
  assert status == 0

def test_cli_with_explicit_values():
  templFile = f"{assetsDir}/sample_template.yml"
  valuesFile = f'{assetsDir}/sample_values.yml'
  status, stdout, stderr = RunCmd([
    "python3",
    f'{jinnyDir}/jinny.py',
    "-i",
    valuesFile,
    "-t",
    templFile,
    "-e",
    "ports.web=8000"
    ])
  
  results = list(yaml.load_all(stdout, Loader=yaml.FullLoader))

  print(stdout)
  print(stderr)
  print(status)
  assert status == 0
  assert results[0]["spec"]["ports"][0]["port"] == 8000

##########################################
# Extensions

extensionsOutput = None

def test_extensions_prep_output():
  global extensionsOutput
  templFile = f"{assetsDir}/filters_template.yml"
  valuesFile = f'{assetsDir}/sample_values.yml'
  status, stdout, stderr = RunCmd([
    "python3",
    f'{jinnyDir}/jinny.py',
    "-i",
    valuesFile,
    "-t",
    templFile,
    ])

  print(stdout)
  print(stderr)
  print(status)
  assert status == 0

  results = yaml.load(stdout, Loader=yaml.FullLoader)
  extensionsOutput = results

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_extension_file_content():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["release_name"] == "testing"

  targetFileContent = f"{assetsDir}/file_content.txt"
  with open(targetFileContent, "r") as f:
    targetFileContentData = f.read()
  
  print('extensionsOutput["file_content"]:')
  print(extensionsOutput["file_content"])
  print('targetFileContentData:')
  print(targetFileContentData)
  assert hash(extensionsOutput["file_content"].strip()) == hash(targetFileContentData.strip())

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_extension_paths():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput['path_extensions_each']
  assert extensionsOutput['path_extensions_each']['cwd']
  assert extensionsOutput['path_extensions_each']['jinny']
  assert extensionsOutput['path_extensions_each']['template']
  assert extensionsOutput['path_extensions_each']['templatedir']
  assert extensionsOutput['path_extensions_each']['home']
  assert isinstance(extensionsOutput['path_extensions_dict'], dict)

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_time_now():
  print(json.dumps(extensionsOutput, indent=2))
  # This will fail in some millisecond, possibly microsecond intervals between minutes, however, given GIL likely always a race condition in this scenario and possibly never encountered
  n = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")
  assert extensionsOutput["time_now"] == n

# As we're reading from stdout
@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_raw_templating():
  templFile = f"{assetsDir}/raw_template.yml"
  valuesFile = f'{assetsDir}/sample_values.yml'

  with open(valuesFile) as f:
    templValsData = f.read()
  templVals = yaml.load(templValsData, Loader=yaml.FullLoader)

  tmplClass = jinny.TemplateHandler(templateName="test_raw_templating", path=templFile)
  tmplClass.Render(templVals)
  res = tmplClass.Result()

  targetFileContent = f"{assetsDir}/file_content.txt"
  with open(targetFileContent, "r") as f:
    targetFileContentData = f.read()
  assert hash(res) == hash(targetFileContentData)

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_nested_template():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["nested_template"]
  assert extensionsOutput["nested_template"]['this'] == "is a nested template"
  assert extensionsOutput["nested_template"]['nested_path_cwd'] == extensionsOutput['path_extensions_each']['cwd']
  assert extensionsOutput["nested_template"]['nested_value'] == extensionsOutput['release_name']

def test_extensions_print():
  templFile = f"{assetsDir}/print_template.txt"
  status, stdout, stderr = RunCmd([
    "python3",
    f'{jinnyDir}/jinny.py',
    "-t",
    templFile,
    ])

  print(f'stdout: {stdout}')
  print(f'stderr: {stderr}')
  print(f'status: {status}')

  assert status == 0
  assert stdout.strip() == "stdout mushrooms"
  assert stderr.strip() == "stderr bacon"

