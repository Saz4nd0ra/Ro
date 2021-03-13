from pymongo import MongoClient
from .config import Config
from . import exceptions
from typing import Union
import dns
import logging
import distutils
import logging

log = logging.getLogger("utils.db")

config = Config()
mongo_url = config.mongodb_url

client = MongoClient(mongo_url)
db = client.adb

DEFAULT_GUILD_CONFIG = {
    "_id": 0,
    "prefix": ">>",
    "adminrole": 0,
    "modrole": 0,
    "reddit_embed": True,
    "automod_role": 0
}

DEFAULT_USER_CONFIG = {"_id": 0,"r34_tags": "", "reddit_name": "", "twitter_name": "", "steam_name": ""}

DEFAULT_LEVEL_CONFIG = {"_id": 0, "current_xp": 0, "current_level": 0}


class Connect(object):
    @staticmethod
    def get_db():
        """Returns our database."""
        return db

# TODO make the whole methods cleaner, probably gonna implement multiple classes

