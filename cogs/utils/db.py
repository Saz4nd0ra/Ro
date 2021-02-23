from pymongo import MongoClient
from .config import Config
import dns
import distutils
import logging

config = Config()
mongo_url = config.mongodb_url

client = MongoClient(mongo_url)
db = client.adb

DEFAULT_GUILD_CONFIG = {
    "_id": 0,
    "prefix": ">>",
    "adminrole": 0,
    "modrole": 0,
    "redditembed": True,
    "automodrole": 0
}

DEFAULT_USER_CONFIG = {"_id": 0,"r34_tags": "", "redditor_url": "", "twitter_url": ""}

DEFAULT_LEVEL_CONFIG = {"_id": 0, "current_xp": 0, "current_level": 0}


class Connect(object):
    @staticmethod
    def get_db():
        """Returns our database."""
        return db

    @staticmethod
    def generate_document(db_name: str, document_id: int):
        """Generates a new document for the given user id."""

        if db_name == "guilds":
            DEFAULT_GUILD_CONFIG["_id"] = document_id
            db.guilds.insert_one(DEFAULT_GUILD_CONFIG)
        elif db_name == "users":
            DEFAULT_USER_CONFIG["_id"] = document_id
            db.users.insert_one(DEFAULT_USER_CONFIG)
        elif db_name == "levels":
            DEFAULT_LEVEL_CONFIG["_id"] = document_id
            db.levels.insert_one(DEFAULT_LEVEL_CONFIG)

    @staticmethod
    def delete_document(db_name: str, document_id: int):
        """Deletes the document for the given guild id."""

        if db_name == "guilds":
            db.guilds.delete_one({"_id": document_id})
        elif db_name == "users":
            db.users.delete_one({"_id": document_id})
        elif db_name == "levels":
            db.levels.delete_one({"_id": document_id})

    @staticmethod
    def update_field_value(db_name: str, document_id: int, field: str, new_setting: str):
        """Updates a field in the user document."""

        if new_setting.isnumeric():
            new_setting = int(new_setting)
        elif new_setting == "True":
            new_setting = True
        elif new_setting == "False":
            new_setting = False

        if db_name == "guilds":
            db.guilds.update_one({"_id": document_id}, {"$set": {field: new_setting}})
        elif db_name == "users":
            db.users.update_one({"_id": document_id}, {"$set": {field: new_setting}})
        elif db_name == "levels":
            db.levels.update_one({"_id": document_id}, {"$set": {field: new_setting}})


    @staticmethod
    def get_field_value(db_name: str, document_id: int, field: str):
        """Returns the field value of a given field in the guilds database."""

        if db_name == "guilds":
            document = db.guilds.find_one({"_id": document_id})
        elif db_name == "users":
            document = db.users.find_one({"_id": document_id})
        elif db_name == "levels":
            document = db.levels.find_one({"_id": document_id})

        return document[field]


