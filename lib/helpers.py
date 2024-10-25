import os
import json
import base64

import lib.log as log

# Make it easy to read a file
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

# Make it easy to read lines in a file
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

# Make it easy to merge two JSON objects
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

# A decorator that "tries" arg1 times, and throws the arg2 message
from functools import wraps

def retry_or_throw(times_allowed, exception_message):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            fails = 0
            while True:
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    log.write(f"{log.colors.fg.red}{e}")

                    fails = fails + 1
                    if fails >= times_allowed:
                        break
                    continue

            raise Exception(f"{exception_message} (Failed {fails} times)")
        return wrapper
    return decorator

# Access a ClientSession singleton:
import aiohttp

http_session = None
def get_http_session():
    global http_session
    if http_session is None:
        http_session = aiohttp.ClientSession()
    return http_session

# https://stackoverflow.com/questions/38408253/way-to-convert-image-straight-from-url-to-base64-without-saving-as-a-file-in-pyt
async def get_attachment_base64(url):
    result      = await get_http_session().get(url)
    attachment  = await result.read()
    return base64.b64encode(attachment).decode("utf-8")
