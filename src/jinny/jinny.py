#!/usr/bin/env python3

##########################################
# Imports

import json
import yaml
import jinja
import argparse

##########################################
# Argparsing
parser = argparse.ArgumentParser(description="Handles templating for jinja templates at a large scale and with multiple inputs")

# Core arguments
parser.add_argument("-v", "--verbose", help="Set output to verbose", action="store_true")
parser.add_argument("-vvv", "--super-verbose", help="Set output to super verbose where this script will print basically everything", action="store_true")
parser.add_argument("-i", "--input-values", help="Add one or more file locations that include input values to the templating", action="append", nargs="*")
parser.add_argument("-t", "--templates", help="Add one or more file locations that contain the templates themselves", action="append", nargs="*")

# Other Arguments
parser.add_argument("-d", "--dump-to-dir", help="Dump completed templateds to a target directory", nargs="1")

args = parser.parse_args()

##########################################
# Variables
