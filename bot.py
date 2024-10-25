from config import *

import discord
import io
import asyncio
import time
import json
import base64
import re

import lib.db as db
import lib.log as log

from lib.log import colors
from lib.helpers import *
from lib.deliverable import Deliverable

intents = discord.Intents(messages=True, guilds=True, message_content=True, reactions=True)
client = discord.Client(intents=intents)

@retry_or_throw(5, "Request stub could not be retrieved")
async def get_request_stub(request_json):
    result = await get_http_session().post(
        f"{SELECTOR_ADDRESS}/v1/stub",
        json=request_json)

    return json.loads(await result.text())

@retry_or_throw(5, "Processed request stub could not be retrieved")
async def get_request_stub_processed(stub_json):
    result =  await get_http_session().post(
        f"{SELECTOR_ADDRESS}/v1/process",
        json = stub_json)

    return json.loads(await result.text())

async def get_message_attachments_as_files(msg):
    discord_files = []

    for a in msg.attachments:
        b64_data = await get_attachment_base64(a.url)
        b64_data = base64.b64decode(b64_data)
        discord_files.append(discord.File(io.BytesIO(b64_data), filename=a.filename))

    return discord_files


async def process_request(stub_json, msg):
    chl         = msg.channel
    time_start  = time.perf_counter()

    await msg.add_reaction(WAITING_EMOJI)
    await chl.typing()

    result = await get_request_stub_processed(stub_json)

    if "output_files" not in result.keys():
        return None

    await chl.typing()



    all_attachments = result["output_files"]

    # Make the response a reply to the user's message if reply_to_user is true:
    reference = None
    if "reply_to_user" in result["all_options"]:
        if result["all_options"]["reply_to_user"] == True:
            reference = msg

    post_is_link = isinstance(all_attachments, str)

    if post_is_link:
        message = f"[Download]({all_attachments})"
        post    = await chl.send(content=message, reference=reference)

    else:

        while True:
            attachments_buffer  = all_attachments[:8]
            discord_files       = []
            
            for a in attachments_buffer:
                base64_str          = a["file_data"]
                base64_bytes        = base64_str.encode("ascii")
                attachment_bytes    = base64.b64decode(base64_bytes)

                f = discord.File(io.BytesIO(attachment_bytes), filename=a["file_name"])
                discord_files.append(f)

            if len(discord_files) < 1: 
                discord_files = None

            post = await chl.send(files=discord_files, content=msg.content, reference=reference)

            if "allow_forward" in result["all_options"]:
                if result["all_options"]["allow_forward"] == True:
                    await post.add_reaction(MAIL_EMOJI)

            del all_attachments[:8]

            if len(all_attachments) < 1:
                break

    if "allow_repeat" in result["all_options"]:
        if result["all_options"]["allow_repeat"] == True:
            await msg.add_reaction(REPEAT_EMOJI)
            if not post_is_link:
                await post.add_reaction(REPEAT_EMOJI)
            
    await msg.remove_reaction(WAITING_EMOJI, client.user)

    time_end    = time.perf_counter()
    time_taken  = time_end - time_start

    return {
        "server_address": result["server_address"],
        "execution_time": result["execution_time"],
        "delivery_time": time_taken
    }

# Discord bot setup
@client.event
async def on_ready():
    print("READY")

@client.event
async def on_message(msg):

    @retry_or_throw(5, "on_message failure")
    async def wrapper():
        chl = msg.channel

        if msg.type != discord.MessageType.default: return
        if msg.author == client.user:               return
        if not hasattr(chl, "topic"):               return
        if chl.topic is None:                       return
        if len(chl.topic) < 1:                      return

        category = ""
        if chl.category is not None:
            category = chl.category.name

        log.write_message(msg)

        request_json = {
            "category":         category,
            "channel_topic":    chl.topic,
            "user_message":     msg.content,
            "user_roles":       [],
            "user":             msg.author.name,
            "all_options":      json_merge({}, read_json("defaults.json"))
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

        stub_info = await get_request_stub(request_json)

        if "stub" in stub_info:
            d = Deliverable.create_from_message(msg)
            d.log_to_database()

            result = await process_request({"stub": stub_info["stub"]}, msg)

            d.execution_time = result["execution_time"]
            d.delivery_time = result["delivery_time"]
            d.processed_on = result["server_address"]
            d.save()

            log.write(colors.fg.green + "Took %.2fs" % result["delivery_time"])

    await wrapper()

@client.event
async def on_raw_reaction_add(rxn):

    @retry_or_throw(5, "on_raw_reaction_add failure")
    async def wrapper():
        chl     = await client.fetch_channel(rxn.channel_id)
        msg     = await chl.fetch_message(rxn.message_id)
        user    = await client.fetch_user(rxn.user_id)
        emoji   = rxn.emoji.name

        if msg.type not in [discord.MessageType.default, discord.MessageType.reply]: return
        if user == client.user:                             return
        if not hasattr(chl, "topic"):                       return
        if chl.topic is None:                               return
        if len(chl.topic) < 1:                              return
        if re.search(r"(http|https):\/\/", msg.content):    return

        category = ""
        if chl.category is not None:
            category = chl.category.name

        # Prepare the 
        request_json = {
            "category":         category,
            "channel_topic":    chl.topic,
            "user_message":     msg.content,
            "user_roles":       [],
            "user":             user.name,
            "all_options":      {},
            "is_repeat":        True
        }

        for role in rxn.member.roles:
            request_json["user_roles"].append(role.name)


        if emoji == REPEAT_EMOJI:
            log.write_reaction(user, msg, emoji)

            if not msg.author.id == client.user.id:
                if len(msg.attachments) > 0:
                    first_attachment = msg.attachments[0]
                    if hasattr(first_attachment, "width") and  hasattr(first_attachment, "height"):
                        image_url = first_attachment.url
                        log.write("Downloading image...")
                        image_data = await get_attachment_base64(image_url)
                        request_json["all_options"]["input_image_data"] = image_data

            stub_info = await get_request_stub(request_json)

            # Ensure that allow_repeat is enabled for this message:
            if "stub" not in stub_info:                             return
            if "all_options" not in stub_info:                      return
            if "allow_repeat" not in stub_info["all_options"]:      return
            if stub_info["all_options"]["allow_repeat"] != True:    return

            d = Deliverable.create_from_reaction(user, msg, emoji)
            d.log_to_database()

            result = await process_request({"stub": stub_info["stub"]}, msg)

            d.execution_time = result["execution_time"]
            d.delivery_time = result["delivery_time"]
            d.processed_on = result["server_address"]
            d.save()

            log.write(colors.fg.green + "Took %.2fs" % result["delivery_time"])

        if emoji == MAIL_EMOJI:
            stub_info = await get_request_stub(request_json)

            if "stub" not in stub_info:                             return
            if "all_options" not in stub_info:                      return
            if "allow_forward" not in stub_info["all_options"]:     return
            if stub_info["all_options"]["allow_forward"] != True:   return

            if len(msg.attachments) < 1: return

            # Convert the message to hashtags so it can easily be copied:
            scrubbed_content = msg.content
            scrubbed_content = re.sub(r"[^A-Za-z0-9 ]", "", scrubbed_content)
            scrubbed_content = re.sub(r"\s+", " ", scrubbed_content)
            scrubbed_content = scrubbed_content.strip()
            scrubbed_content = re.sub(r"(^|\s)", " #", scrubbed_content)
            scrubbed_content = scrubbed_content.strip()

            files = await get_message_attachments_as_files(msg)

            await user.send(content=scrubbed_content, files=files)


    await wrapper()

# Begin the Discord bot:
client.run(read_file("token.txt"))
