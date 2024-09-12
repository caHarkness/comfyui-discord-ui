from config import *

import os
import os.path
import discord
import io
import asyncio
import threading
import time
import json
import base64

import lib.sdxl as sdxl
import lib.db as db
import lib.log as log

from lib.log import colors
from lib.helpers import *
from lib.deliverable import Deliverable
from lib.request import Request

intents = discord.Intents(messages=True, guilds=True, message_content=True, reactions=True)
client = discord.Client(intents=intents)

'''
Initial setup:
'''
mkdir("output")

'''
Discord bot setup:
'''
@client.event
async def on_ready():
    print("READY")


async def handle_request(request_json, msg):
    chl = msg.channel

    time_start = time.perf_counter()

    await msg.add_reaction(WAITING_EMOJI)


    result = requests.post(
        f"http://127.0.0.1:5000/v1/base64",
        json = request_json)

    result = json.loads(result.text)

    #result = await req.get_images()
    images = result["output_files"]

    while True:
        new_images = images[:8]
        discord_files = []
        
        for i in new_images:
            base64_str = i["image_data"]
            base64_bytes = base64_str.encode("ascii")
            image_bytes = base64.b64decode(base64_bytes)


            f = discord.File(io.BytesIO(image_bytes), filename=i["file_name"])
            discord_files.append(f)

        post = await chl.send(files=discord_files, content=msg.content)
        del images[:8]

        if len(images) < 1:
            break

    #if "allow_repeat" in req.all_options.keys() and req.all_options["allow_repeat"] == True:
    #    await msg.add_reaction(REPEAT_EMOJI)
    #    await post.add_reaction(REPEAT_EMOJI)

    #await post.add_reaction(REPEAT_EMOJI)
    await msg.remove_reaction(WAITING_EMOJI, client.user)

    time_end = time.perf_counter()
    time_taken = time_end - time_start

    return {
        "server_address": result["server_address"],
        "execution_time": result["execution_time"],
        "delivery_time": time_taken
    }

@client.event
async def on_message(msg):
    chl = msg.channel

    if not hasattr(chl, "topic"):
        return

    if chl.topic is None or len(chl.topic) < 1:
        return

    if msg.author == client.user:
        return

    category = ""
    if chl.category is not None:
        category = chl.category.name

    request_json = {
        "category":         category,
        "channel_topic":    chl.topic,
        "user_message":     msg.content,
        "user_roles":       [],
        "user":             msg.author.name,
        "all_options":      {}
    }

    if not msg.author.id == client.user.id:
        if len(msg.attachments) > 0:
            first_attachment = msg.attachments[0]
            if hasattr(first_attachment, "width") and  hasattr(first_attachment, "height"):
                image_url = first_attachment.url
                log.write("Downloading image...")
                image_data = await get_attachment_base64(image_url)
                request_json["all_options"]["input_image_data"] = image_data

    for role in msg.author.roles:
        request_json["user_roles"].append(role.name)

    # get the API all_options here:



    d = Deliverable.create_from_message(msg)
    d.log_to_database()

    #result = await handle_request(req, msg)
    # get images here:

    result = await handle_request(request_json, msg)

    d.execution_time = result["execution_time"]
    d.delivery_time = result["delivery_time"]
    d.processed_on = result["server_address"]
    d.save()

    log.write(colors.fg.green + "Took %.2fs" % result["delivery_time"])



@client.event
async def on_raw_reaction_add(rxn):
    chl = await client.fetch_channel(rxn.channel_id)
    msg = await chl.fetch_message(rxn.message_id)
    user = await client.fetch_user(rxn.user_id)
    emoji = rxn.emoji.name

    if not hasattr(chl, "topic"):
        return

    if chl.topic is None or len(chl.topic) < 1:
        return

    if user == client.user:
        return

    category = ""
    if chl.category is not None:
        category = chl.category.name

    if emoji == REPEAT_EMOJI:
        # Restric access to the recycle/rerun feature:
        # allow = await member_has_role(rxn.member, REPEAT_EMOJI)
        # if not allow:
        #     return

        request_json = {
            "category":         category,
            "channel_topic":    chl.topic,
            "user_message":     msg.content,
            "user_roles":       [],
            "user":             user.name,
            "all_options":      {},
            "is_repeat":        True
        }

        if not msg.author.id == client.user.id:
            if len(msg.attachments) > 0:
                first_attachment = msg.attachments[0]
                if hasattr(first_attachment, "width") and  hasattr(first_attachment, "height"):
                    image_url = first_attachment.url
                    log.write("Downloading image...")
                    image_data = await get_attachment_base64(image_url)
                    request_json["all_options"]["input_image_data"] = image_data

        for role in rxn.member.roles:
            request_json["user_roles"].append(role.name)

        # get the API all_options here:



        d = Deliverable.create_from_reaction(user, msg, emoji)
        d.log_to_database()

        #result = await handle_request(req, msg)
        # get images here:

        result = await handle_request(request_json, msg)

        d.execution_time = result["execution_time"]
        d.delivery_time = result["delivery_time"]
        d.processed_on = result["server_address"]
        d.save()

        log.write(colors.fg.green + "Took %.2fs" % result["delivery_time"])

'''
Begin the Discord bot magic:
'''
client.run(read_file("token.txt"))
