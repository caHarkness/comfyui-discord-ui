from lib.helpers import *

# The colors class below is from:
# https://www.geeksforgeeks.org/print-colors-python-terminal
class colors:
    reset = "\033[0m"
    bold = "\033[01m"
    disable = "\033[02m"
    underline = "\033[04m"
    reverse = "\033[07m"
    strikethrough = "\033[09m"
    invisible = "\033[08m"
     
    class fg:
        white = "\033[97m"
        black = "\033[30m"
        red = "\033[31m"
        green = "\033[32m"
        orange = "\033[33m"
        blue = "\033[34m"
        purple = "\033[35m"
        cyan = "\033[36m"
        lightgrey = "\033[37m"
        darkgrey = "\033[90m"
        lightred = "\033[91m"
        lightgreen = "\033[92m"
        yellow = "\033[93m"
        lightblue = "\033[94m"
        pink = "\033[95m"
        lightcyan = "\033[96m"

    class bg:
        black = "\033[40m"
        red = "\033[41m"
        green = "\033[42m"
        orange = "\033[43m"
        blue = "\033[44m"
        purple = "\033[45m"
        cyan = "\033[46m"
        lightgrey = "\033[47m"

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

def write(user_input):
    timestamp = get_timestamp_log()
    output = f"{colors.fg.darkgrey}[{timestamp}] {user_input}{colors.reset}"
    print(output)

def write_message(msg):
    cat = f"{msg.channel.category.name}/" if msg.channel.category else ""
    author = f"{msg.author.name}#{msg.author.discriminator}" if int(msg.author.discriminator) > 0 else msg.author.name
    output = f"[/{msg.channel.guild.name}/{cat}{msg.channel.name}/{author}] {colors.fg.lightgrey}{msg.content}"
    write(output)

def write_reaction(user, msg, emoji):
    cat = f"{msg.channel.category.name}/" if msg.channel.category else ""
    user_name = f"{user.name}#{user.discriminator}" if int(user.discriminator) > 0 else user.name
    output = f"[/{msg.channel.guild.name}/{cat}#{msg.channel.name}/{user_name}] {colors.fg.lightgrey}Reacted {colors.fg.yellow}{emoji}{colors.fg.lightgrey} to {msg.content}"
    write(output)
