'''
This module is the interface to ComfyUI and all the functions we need from it
'''

import websocket
import uuid
import json
import requests
import io


'''
Method for getting the least busy ComfyUI server in an array of ComfyUI hosts
'''
def get_least_busy_address(server_addresses):
    address_selection = None
    selection_score = None

    for a in server_addresses:
        if address_selection is None:
            address_selection = a

        try:
            resp = requests.get(f"http://{a}/queue")
            resp_json = resp.json()
            score = len(resp_json["queue_running"]) + len(resp_json["queue_pending"])

            if selection_score is None or score < selection_score:
                address_selection = a
                selection_score = score
        except:
            continue

    return address_selection

def queue_prompt(prompt, client_id, server_address):
    resp = requests.post(
        f"http://{server_address}/prompt",
        json = {
            "prompt": prompt,
            "client_id": client_id
        })

    return resp.json()

from urllib.request import urlopen as urlopen
from urllib.parse import urlencode as urlencode

def get_image(filename, subfolder, folder_type, server_address):
    params = urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    address = f"http://{server_address}/view?{params}"

    with urlopen(address) as resp:
        return resp.read()

def get_history(prompt_id, server_address):
    address = f"http://{server_address}/history/{prompt_id}"

    with urlopen(address) as resp:
        return json.loads(resp.read())

def get_images(ws, prompt, client_id, server_address):
    prompt_id = queue_prompt(prompt, client_id, server_address)["prompt_id"]
    output_images = {}

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id, server_address)[prompt_id]

    for o in history["outputs"]:
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            if "images" in node_output:
                images_output = []
                for image in node_output["images"]:
                    image_data = get_image(image["filename"], image["subfolder"], image["type"], server_address)
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images
