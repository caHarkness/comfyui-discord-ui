from config import *

import os
import os.path
import discord
import io
import asyncio
import threading
import time

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

async def member_has_role(member, role_name):
    allow = False
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role in member.roles:
        allow = True
    return allow

async def handle_request(req, msg):
    chl = msg.channel

    time_start = time.perf_counter()

    await msg.add_reaction(WAITING_EMOJI)

    #result = await sdxl.get_image_data_async(channel_topic=chl.topic, user_input=msg.content)
    #result = await sdxl.get_image_data_async(channel_topic=chl.topic, user_input=msg)

    result = await req.get_images()
    images = result["output_files"]

    while True:
        new_images = images[:8]
        discord_files = []
        
        for i in new_images:
            f = discord.File(io.BytesIO(i["image_data"]), filename=i["file_name"])
            discord_files.append(f)

        post = await chl.send(files=discord_files, content=msg.content)
        del images[:8]

        if len(images) < 1:
            break

    if "allow_repeat" in req.all_options.keys() and req.all_options["allow_repeat"] == True:
        await msg.add_reaction(REPEAT_EMOJI)
        await post.add_reaction(REPEAT_EMOJI)

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

    all_options = {}
    req = Request.create({
        "category": category,
        "channel_topic": chl.topic,
        "user_message": msg.content,
        "all_options": all_options
    })

    # A first iteration is needed to check if attachments are processed:
    req.get_options_json()

    # If we know a workflow .json file exists, allow, otherwise stop logic here:
    if not req.has_workflow_json_file():
        return

    if "attachments" in req.all_options.keys() and req.all_options["attachments"] == True:
        if len(msg.attachments) > 0:
            first_attachment = msg.attachments[0]
            if hasattr(first_attachment, "width") and hasattr(first_attachment, "height"):
                image_url = first_attachment.url
                log.write("Downloading image...")
                image_data = await get_attachment_base64(image_url)
                all_options["input_image_data"] = image_data
                print(image_data)

    # A second iteration through is needed to allow the chain to remove the attachment data:
    req.get_options_json(all_options)

    # Check user roles and apply them:
    try:
        for fname in os.listdir("roles"):
            matches = re.search(r"([A-Za-z0-9_ ]{1,})\.json$", fname)
            role_name = matches.group(1)
            has_role = await member_has_role(msg.author, role_name)

            if has_role:
                req.merge_options(read_json(f"roles/{role_name}.json", {}))
                # log.write(f"Merged role: {role_name}")
    except:
        pass

    # Try loading custom user options by user's id, then user's name:
    req.merge_options(read_json(f"users/{msg.author.id}.json", {}))
    author = f"{msg.author.name}#{msg.author.discriminator}" if int(msg.author.discriminator) > 0 else msg.author.name
    req.merge_options(read_json(f"users/{author}.json", {}))

    # if "allow_repeat" in req.all_options.keys() and req.all_options["allow_repeat"] == True:
    #    await msg.add_reaction(REPEAT_EMOJI)

    req.parse_input()
    req.get_workflow_json()

    log.write_message(msg)

    d = Deliverable.create_from_message(msg)
    d.set_request_object(req)
    d.log_to_database()

    result = await handle_request(req, msg)

    d.processed_on = result["server_address"]
    d.execution_time = result["execution_time"]
    d.delivery_time = result["delivery_time"]
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

    all_options = {}
    req = Request.create({
        "category": category,
        "channel_topic": chl.topic,
        "user_message": msg.content,
        "all_options": all_options
    })

    req.get_options_json()

    if not req.has_workflow_json_file():
        return

    if emoji == REPEAT_EMOJI:
        # Restric access to the recycle/rerun feature:
        # allow = await member_has_role(rxn.member, REPEAT_EMOJI)
        # if not allow:
        #     return

        if "attachments" in req.all_options.keys() and req.all_options["attachments"] == True:
            if not msg.author.id == client.user.id:
                if len(msg.attachments) > 0:
                    first_attachment = msg.attachments[0]
                    if hasattr(first_attachment, "width") and  hasattr(first_attachment, "height"):
                        image_url = first_attachment.url
                        log.write("Downloading image...")
                        image_data = await get_attachment_base64(image_url)
                        all_options["input_image_data"] = image_data
                        print(image_data)

        req.get_options_json(all_options)

        # Check user roles and apply them:
        try:
            for fname in os.listdir("roles"):
                matches = re.search(r"([A-Za-z0-9_ ]{1,})\.json$", fname)
                role_name = matches.group(1)
                has_role = await member_has_role(rxn.member, role_name)

                if has_role:
                    req.merge_options(read_json(f"roles/{role_name}.json", {}))
                    # log.write(f"Merged role: {role_name}")
        except:
            pass

        # Try loading custom user options by user's id, then user's name:
        req.merge_options(read_json(f"users/{user.id}.json", {}))
        author = f"{msg.author.name}#{user.discriminator}" if int(user.discriminator) > 0 else user.name
        req.merge_options(read_json(f"users/{author}.json", {}))

        if "allow_repeat" not in req.all_options.keys() or req.all_options["allow_repeat"] == False:
            return
        
        req.parse_input()
        req.get_workflow_json()

        log.write_reaction(user, msg, emoji)

        d = Deliverable.create_from_reaction(user, msg, emoji)
        d.set_request_object(req)
        d.log_to_database()

        result = await handle_request(req, msg)

        d.execution_time = result["execution_time"]
        d.delivery_time = result["delivery_time"]
        d.processed_on = result["server_address"]
        d.save()

        log.write(colors.fg.green + "Took %.2fs" % result["delivery_time"])

'''
Begin the Discord bot magic:
'''
client.run(read_file("token.txt"))
