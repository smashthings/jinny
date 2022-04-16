#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/jinny')))


import jinny_merging

jinny_merging.VerboseSetting = 2

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
