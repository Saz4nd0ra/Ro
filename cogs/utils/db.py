from typing import Coroutine
from pymongo import MongoClient
import logging
import logging

log = logging.getLogger("utils.db")

DEFAULT_GUILD_CONFIG = {
    "_id": 0,
    "prefix": ">>",
    "adminrole": 0,
    "modrole": 0,
    "auto_embed": True,
    "newmember_role": 0
}

DEFAULT_USER_CONFIG = {"_id": 0,"r34_tags": "", "reddit_name": ""}


class RoDBClient():
    def __init__(self, mango_url: str):
        self.client = MongoClient(mango_url)
        self.db = self.client.ro


    def generate_guild_config(self, guild_id: int) -> Coroutine:

        DEFAULT_GUILD_CONFIG["_id"] = guild_id
        self.db.guilds.insert_one(DEFAULT_GUILD_CONFIG)

        log.info(f"Config generated.. _id: {guild_id}")

    def generate_user_config(self, user_id: int) -> Coroutine:

        DEFAULT_GUILD_CONFIG["_id"] = user_id
        self.db.guilds.insert_one(DEFAULT_GUILD_CONFIG)

        log.info(f"Config generated.. _id: {user_id}")

    