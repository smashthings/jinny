#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/jinny')))

import yaml
import traceback
import subprocess

import jinny
import inspect

jinny.VerboseSetting = 2

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

  try:
    assertingYaml = yaml.load_all(res, Loader=yaml.FullLoader)
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

