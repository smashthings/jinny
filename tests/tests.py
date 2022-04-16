#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/jinny')))


import jinny_merging
import jinny_logging

jinny_merging.VerboseSetting = 2
jinny_merging.LoggingFunction = jinny_logging.Log

##########################################
# Merge Tests

def test_combine_lists():
  jinny_merging.CombineLists = True
  res = jinny_merging.CombineValues(["one", "two"], ["ay", "be"], 'test_combine_lists')
  assert res == ["one", "two", "ay", "be"]

def test_replace_lists():
  jinny_merging.CombineLists = False
  res = jinny_merging.CombineValues(["one", "two"], ["ay", "be"], 'test_replace_lists')
  assert res == ["ay", "be"]

def test_merging_dicts():
  res = jinny_merging.CombineValues({
    "first": True
  }, {
    "second": "please"
  }, 'test_merging_dicts')
  assert res["first"] == True
  assert res["second"] == "please"

def test_nested_dicts():
  res = jinny_merging.CombineValues({
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
  res = jinny_merging.CombineValues({
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
  jinny_merging.SetNestedResource(origResource, ["dicts", "0", "nest_one", "mushrooms"], False)
  jinny_merging.SetNestedResource(origResource, ["dicts", "1", "added_resource"], 4)
  jinny_merging.SetNestedResource(origResource, ["dicts", "1", "toppings", "0", "dict_dict", "other"], False)
  assert origResource["dicts"][0]['nest_one']['mushrooms'] == False
  assert origResource["dicts"][1]['added_resource'] == 4
  assert origResource["dicts"][1]['toppings'][0]['dict_dict']['other'] == False

def test_generated_nest():
  res = jinny_merging.GenerateNestedDict(["nest_one", "nest_two", "nest_three", "key"], True)
  assert res["nest_one"]["nest_two"]["nest_three"]["key"] == True
