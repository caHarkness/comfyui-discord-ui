import os
import json



'''
Read an entire file into a string:
'''
def read_file(path, default_value=""):
    try:
        text = ""
        with open(path, "r") as f:
            text = f.read()

        text = text.strip()
        return text
    except:
        pass

    return default_value

# Make it easy to read a json file
def read_json(path, default_value={}):
    if os.path.isfile(path):
        try:
            json_string = read_file(path, default_value)
            json_dict = json.loads(json_string)
            return json_dict
        except:
            pass

    return default_value

# Make it easy to read a json file
def read_lines(path, default_value=[]):
    if os.path.isfile(path):
        try:
            output = []
            text_string = read_file(path, default_value)
            parts = f"{text_string}\n".split("\n")

            for part in parts:
                part = part.strip()
                if len(part) > 0:
                    output.append(part)

            return output
        except:
            pass

    return default_value

# Return first non-null value
# https://stackoverflow.com/a/16247152
def coalesce(*arg):
  for el in arg:
    if el is not None:
      return el
  return None

# Allows function to be awaited for without blocking?
# https://stackoverflow.com/a/50450553
import asyncio
from functools import partial, wraps

def to_thread(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        callback = partial(func, *args, **kwargs)
        return await asyncio.to_thread(callback)
    return wrapper


import time
from datetime import datetime

def get_timestamp():
    now = datetime.now()
    timestamp = now.strftime("%f")[:-3]
    timestamp = now.strftime("%Y%m%d_%H%M%S_") + timestamp
    return timestamp

def get_timestamp_log():
    now = datetime.now()
    timestamp = now.strftime("%f")[:-3]
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.") + timestamp
    return timestamp

def json_merge(a, b):
    if b is None:
        return a

    output = a
    for k in b:
        # Try to get rid of the key in output if the additional json object has a null value for that key:
        if b[k] is None:
            output.pop(k, None)
        else:
            output[k] = b[k]
    return output

def channel_topic_to_defaults(input_str):
    output = {}
    output = json_merge(output, read_json("defaults.json", {}))

    input_str = input_str + ","
    parts = input_str.split(",")
    
    for part in parts:
        actual_part = part.strip()

        if len(actual_part) < 1:
            continue

        output = json_merge(output, read_json(f"defaults/{actual_part}.json", {}))

    return output

def channel_topic_first_part(input_str):
    input_str = input_str + ","
    first_part = input_str.split(",")[0]
    first_part = first_part.strip()
    return first_part

def channel_topic_workflow(input_str):
    first_part = channel_topic_first_part(input_str)
    return read_json(f"workflows/{first_part}.json", {})

def channel_topic_workflow_text(input_str):
    first_part = channel_topic_first_part(input_str)

    f = open(f"workflows/{first_part}.json")
    workflow_json = f.read()
    f.close()

    return workflow_json

def mkdir(path):
    try:
        os.mkdir(path)
    except:
        pass


import re

def make_replacements(input_string, pat, replacement):
    if input_string is None:
        return input_string

    using = input_string
    match = re.search(pat, using)
    while match is not None:
        using = re.sub(pat, str(replacement), using)
        match = re.search(pat, using)
    return using

# https://stackoverflow.com/questions/38408253/way-to-convert-image-straight-from-url-to-base64-without-saving-as-a-file-in-pyt
import base64
import requests

@to_thread
def get_attachment_base64(url):
    return base64.b64encode(requests.get(url).content).decode("utf-8")
