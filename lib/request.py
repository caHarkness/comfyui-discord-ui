from config import *

import json
import websocket
import uuid
import random

import lib.db as db
import lib.log as log
import lib.sdxl as sdxl
import lib.parser as parser

from lib.helpers import *

'''
A method for scrubbing user input, ridding it of undesirable characters:
'''
def safe_user_input(input_string):
    output = input_string
    output = re.sub(r"[^A-Za-z0-9 _\(\)\.,:>-]", "", output)
    return output

def alter_png(full_path, new_info):
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo

    target = Image.open(full_path)
    metadata = PngInfo()

    for i in new_info:
        metadata.add_text(i["key"], i["value"])

    target.save(full_path, pnginfo=metadata)

def safe_file_name(input_string):
    output = input_string
    output = re.sub(r" ", "_", output)
    output = re.sub(r"[^A-Za-z0-9_]", "", output)
    output = re.sub(r"[_]{2,}", "_", output)
    output = output[:200]
    output = f"{output}_" + str(random.randint(10000000, 99999999))
    return output

class Request:
    def __init__(self):
        # do nothing
        self.test = 1

    def create(options):
        r = Request()

        r.category = options["category"]
        r.channel_topic = options["channel_topic"]
        r.user_message = options["user_message"]
        r.all_options = {}
        r.workflow_name = None
        r.workflow_json = None

        if "all_options" in options.keys():
            r.all_options = options["all_options"]

        r.user_message = safe_user_input(r.user_message)

        return r

    def merge_options(self, options):
        if self.all_options is None:
            self.all_options = {}

        self.all_options = json_merge(self.all_options, options)

    def get_options_json(self, set_all_options=None):
        
        if set_all_options is not None:
            self.all_options = set_all_options

        # Start all_options with defaults:
        self.all_options = json_merge(self.all_options, read_json("defaults.json", {}))

        # Apply channel topic token options:
        channel_topic_tokens = self.channel_topic.split(CHANNEL_TOPIC_TOKEN_DELIMITER)

        for token in channel_topic_tokens:
            token = token.strip()

            if len(token) < 1:
                continue

            # Set the workflow name to the first token 
            if self.workflow_name is None:
                self.workflow_name = token

            self.all_options = json_merge(self.all_options, read_json(f"defaults/{token}.json", {}))

        # Apply category name options
        self.all_options = json_merge(self.all_options, read_json(f"categories/{self.category}.json", {}))

        # Process user message and merge
        # user_message_json = parser.parse_input(self.user_message, self.all_options)
        # self.all_options = json_merge(self.all_options, user_message_json)

        return self.all_options

    # Process user message and merge
    def parse_input(self):
        if self.all_options is None:
            self.all_options = {}

        user_message_json = parser.parse_input(self.user_message, self.all_options)
        self.all_options = json_merge(self.all_options, user_message_json)

    def has_workflow_json_file(self):
        return os.path.isfile(f"workflows/{self.workflow_name}.json")

    def get_workflow_json(self):
        json_text = read_file(f"workflows/{self.workflow_name}.json", "{}")

        if "seed" not in self.all_options.keys():
            self.all_options["seed"] = random.randint(10000000, 99999999)

        # Modify the ComfyUI API-formatted workflow json and replace __words__ with all_options["words"]:
        for k in self.all_options.keys():
            if not isinstance(self.all_options[k], (list, dict)):
                json_text = make_replacements(json_text, rf"__{k}__", self.all_options[k])

        self.workflow_json = json.loads(json_text)
        return self.workflow_json

    @to_thread
    def get_images(self):



        time_start = time.perf_counter()

        server_address = sdxl.get_least_busy_address(self.all_options["server_addresses"])
        client_id = str(uuid.uuid4())

        ws = websocket.WebSocket()
        ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
        images = sdxl.get_images(ws, self.workflow_json, client_id, server_address)
        

        output_files = []

        for node_id in images:
            for image_data in images[node_id]:
                timestamp = get_timestamp()
                file_name = f"{timestamp}_" + safe_file_name(self.user_message)
                file_name = f"{file_name}.png"

                # Handle forced spoiler:
                if "force_spoiler" in self.all_options:
                    if self.all_options["force_spoiler"] == True:
                        file_name = f"SPOILER_{file_name}"
     
                # Handle suggested spoiler:
                elif "add_spoiler" in self.all_options:
                    use_spoiler = False

                    if self.all_options["add_spoiler"] == True:
                        bad_words = read_lines("assets/bad_words.txt", [])

                        for w in bad_words:
                            if w.lower() in self.user_message.lower():
                                use_spoiler = True
                                break

                    if use_spoiler == True:
                        file_name = f"SPOILER_{file_name}"

                full_path = f"output/{file_name}"

                i = open(full_path, "wb")
                i.write(image_data)
                i.close()

                alter_png(full_path, [
                    {"key": "channel_topic", "value": self.channel_topic},
                    {"key": "user_message", "value": self.user_message},
                ])

                i = open(full_path, "rb")
                image_data = i.read()
                i.close()

                output_files.append({
                    "file_name": file_name,
                    "image_data": image_data
                })

        time_end = time.perf_counter()
        time_taken = time_end - time_start

        return {
            "server_address": server_address,
            "output_files": output_files,
            "execution_time": time_taken
        }
