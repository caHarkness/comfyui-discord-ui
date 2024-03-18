import json

import lib.db as db
import lib.log as log

class Deliverable:
    def __init__(self):
        # do nothing
        self.test = 1

    def create_from_message(msg):
        d = Deliverable()

        chl = msg.channel

        d.id = None
        d.server_name = chl.guild.name
        d.server_id = chl.guild.id
        d.category_name = chl.category.name if chl.category else None
        d.category_id = chl.category.id if chl.category else None
        d.channel_name = chl.name
        d.channel_topic = chl.topic
        d.channel_id = chl.id
        d.user_name = None
        d.user_id = None
        d.author_name = f"{msg.author.name}#{msg.author.discriminator}"
        d.author_id = msg.author.id
        d.message = msg.content
        d.reaction = None
        d.execution_time = None
        d.delivery_time = None
        d.processed_on = None

        return d

    def create_from_reaction(user, msg, emoji):
        d = Deliverable()

        chl = msg.channel

        d.id = None
        d.server_name = chl.guild.name
        d.server_id = chl.guild.id
        d.category_name = chl.category.name if chl.category else None
        d.category_id = chl.category.id if chl.category else None
        d.channel_name = chl.name
        d.channel_topic = chl.topic
        d.channel_id = chl.id
        d.user_name = f"{user.name}#{user.discriminator}"
        d.user_id = user.id
        d.author_name = f"{msg.author.name}#{msg.author.discriminator}"
        d.author_id = msg.author.id
        d.message = msg.content
        d.reaction = emoji
        d.execution_time = None
        d.delivery_time = None
        d.processed_on = None

        return d


    def log_to_database(self):
        db.query("""
            INSERT into master_log (server_name, server_id, category_name, category_id, channel_name, channel_topic, channel_id, user_name, user_id, author_name, author_id, message, reaction, execution_time, delivery_time, processed_on)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            self.server_name,
            self.server_id,
            self.category_name,
            self.category_id,
            self.channel_name,
            self.channel_topic,
            self.channel_id,
            self.user_name,
            self.user_id,
            self.author_name,
            self.author_id,
            self.message,
            self.reaction,
            self.execution_time,
            self.delivery_time,
            self.processed_on
        ])

        self.id = db.query("select last_insert_id() as val")[0]["val"]

    def save(self):
        result = db.query("""
            UPDATE master_log
            set
                execution_time = %s,
                delivery_time = %s,
                processed_on = %s
            where
                id = %s
        """, [
            self.execution_time,
            self.delivery_time,
            self.processed_on,
            self.id
        ])
