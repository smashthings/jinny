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

def test_cli_with_env_file_parsing():
  templFile = f"{assetsDir}/sample_env_values.yml"
  valuesFile = f'{assetsDir}/sample_env_values.env'
  status, stdout, stderr = RunCmd([
    "python3",
    f'{jinnyDir}/jinny.py',
    "-i",
    valuesFile,
    "-t",
    templFile
    ])
  
  results = list(yaml.load_all(stdout, Loader=yaml.FullLoader))

  print(stdout)
  # print(stderr)
  # print(status)
  assert status == 0
  assert results[0]['b64_encoded_multiline'] == 'bm9vbmUgc2hvdWxkIHJlYWxseSBiZSBkb2luZyB0aGlzCmJ1dCBqaW5ueSBtYWtlcyBhIHRva2VuIGVmZm9ydAp0byBjb21iaW5lIG11bHRpbGluZSBlbnZpcm9ubWVudCB2YXJpYWJsZXMKanVzdCBkb24ndCBwdXQgYW4gZXF1YWxzIGNoYXJhY3RlciBpbiBpdCBmZnM='
  assert results[0]['name'] == 'frank the big old tank'
  assert results[0]['hot_tip'] == 'you should send me some wine gums'

  # This strips from the fed in value as the yaml parser adds a new line. Parsing into parsing into parsing into other parsing
  # Seriously just base64 encode your junk
  assert results[0]['multiline'].rstrip('\n') == '''noone should really be doing this\nbut jinny makes a token effort\nto combine multiline environment variables\njust don't put an equals character in it ffs'''



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
    "--unsafe",
    "-i",
    valuesFile,
    "-t",
    templFile,
    ])

  print(stdout)
  print(stderr)
  print(status)
  assert status == 0

  results = yaml.load(stdout, Loader=yaml.SafeLoader)
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

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_prompt_envvar():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput['prompt_envvar'] == os.environ['HOME']
  assert extensionsOutput['no_envvar_default'] == 'ketchup'

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_time_now():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["list_files"]
  assert extensionsOutput["list_files_recursive"]
  assert extensionsOutput["list_files"]["test1.txt"] == "test1"
  assert extensionsOutput["list_files_recursive"]["test1.txt"] == "test1"
  assert extensionsOutput["list_files_recursive"]["test2.txt"] == "test2"
  assert extensionsOutput["list_files_recursive"]["test3.txt"] == "test3"
  assert extensionsOutput["list_files_recursive"]["test4.txt"] == "test4"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_removeprefix():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["removeprefix"] == "factory"
  assert extensionsOutput["dontremoveprefix"] == "mushroomfactory"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_removesuffix():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["removesuffix"] == "mushroomfact"
  assert extensionsOutput["dontremovesuffix"] == "mushroomfactory"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_censor():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["censored_fixed_length"] == "***"
  assert extensionsOutput["censored_different_vals"] == "XXXX"
  assert extensionsOutput["censored_middle_only"] == "ca*******er"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_base64():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["b64encode"] == "cG90dXM6MDAwMDAwMDA="
  assert extensionsOutput["b64decode"] == "potus:00000000"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_b64file():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["b64file"] == "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"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_getext():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["getext_period"] == ".txt"
  assert extensionsOutput["getext_no_period"] == "txt"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_removeext():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["removeext_short"] == "this"
  assert extensionsOutput["removeext_long"] == "/path/is/this"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_newlinetr():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["newlinetr"] == "this should be a html break here and not a new line <br /> run on to a new sentence"
  assert extensionsOutput["newlinetr_custom"] == "this should be a newcustom  line run on sentence on one line"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_currency():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["currency_usd_str"] == "$73,845,400.32"
  assert extensionsOutput["currency_usd_float"] == "$73,845,400.32"
  assert extensionsOutput["currency_gbp"].encode().decode('utf-8') == "£73,845,400.32"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_is_file():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["is_file_check"] == "file found!"
  assert extensionsOutput["is_file_check_failed"] == "file NOT found!"
  assert extensionsOutput["is_dir_check"] == "dir found!"
  assert extensionsOutput["is_dir_check_failed"] == "dir NOT found!"

@pytest.mark.skipif(extensionsOutput != None, reason="Failed to run prior command for output")
def test_unsafe_cmd():
  print(json.dumps(extensionsOutput, indent=2))
  assert extensionsOutput["unsafe_cmd"] == "big fish"

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

