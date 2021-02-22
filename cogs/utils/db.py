from pymongo import MongoClient
from .config import Config
import dns
import logging
config = Config()
mongo_url = config.mongodb_url

client = MongoClient(mongo_url)
db = client.adb

DEFAULT_GUILD_CONFIG = {"_id": 0, "prefix": ">>", "adminrole": 0, "modrole": 0, "reddit_embed": True}

DEFAULT_USER_CONFIG = {"_id": 0, "nsfw_blacklist": "-tag1 -tag2"}


class Connect(object):
    
    @staticmethod
    def get_db():
        """Returns our database."""
        return db

    @staticmethod
    def generate_guild_document(guild_id):
        """Generates a new document for the given guild id."""

        DEFAULT_GUILD_CONFIG["_id"] = guild_id

        db.guilds.insert_one(DEFAULT_GUILD_CONFIG)

    @staticmethod
    def generate_user_document(user_id):
        """Generates a new document for the given user id."""

        DEFAULT_USER_CONFIG["_id"] = user_id

        db.users.insert_one(DEFAULT_USER_CONFIG)

    @staticmethod
    def update_user_field(user_id, field, new_setting):
        """Updates a field in the user document."""

        db.users.update_one({"_id": user_id}, {"$set":{field: new_setting}})

    @staticmethod
    def update_guild_field(guild_id, field, new_setting):
        """Updates a field in the user document."""

        db.guilds.update_one({"_id": guild_id}, {"$set":{field: new_setting}})

    @staticmethod
    def get_guild_field_value(guild_id, field):
        """Returns the field value of a given field in the guilds database."""

        document = db.guilds.find_one({'_id': guild_id})

        return document[field]

    @staticmethod
    def get_user_field_value(user_id, field: str):
        """Returns the field value of a given field in the users database."""

        document = db.users.find_one({'_id': user_id})

        return document[field]
    







