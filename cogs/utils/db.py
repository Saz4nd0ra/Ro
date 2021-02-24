from pymongo import MongoClient
from .config import Config
from . import exceptions
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

        log.info(f"Config generated.. _id: {document_id}")

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

        current_setting = Connect.get_field_value(db_name=db_name, document_id=document_id, field=field)

        if type(current_setting) != type(new_setting): # checking if types equal
            raise exceptions.TypesNotEqual

        if db_name == "guilds":
            try:
                db.guilds.update_one({"_id": document_id}, {"$set": {field: new_setting}})
            except TypeError:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                log.info(f"Config generated.. _id: {document_id}")
                raise exceptions.MongoError
            finally:
                db.guilds.update_one({"_id": document_id}, {"$set": {field: new_setting}})
        elif db_name == "users":
            try:
                db.users.update_one({"_id": document_id}, {"$set": {field: new_setting}})
            except TypeError:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                log.info(f"Config generated.. _id: {document_id}")
                raise exceptions.MongoError
            finally:
                db.users.update_one({"_id": document_id}, {"$set": {field: new_setting}})
        elif db_name == "levels":
            try:
                db.levels.update_one({"_id": document_id}, {"$set": {field: new_setting}})
            except TypeError:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                log.info(f"Config generated.. _id: {document_id}")
                raise exceptions.MongoError
            finally:
                db.levels.update_one({"_id": document_id}, {"$set": {field: new_setting}})

    @staticmethod
    def get_field_value(db_name: str, document_id: int, field: str):
        """Returns the field value of a given field in the guilds database."""

        if db_name == "guilds":
            if (document := db.guilds.find_one({"_id": document_id})) is not None:
                return document[field]
            else:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                Connect.get_field_value(db_name=db_name, document_id=document_id, field=field)
        elif db_name == "users":
            if (document := db.users.find_one({"_id": document_id})) is not None:
                return document[field]
            else:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                Connect.get_field_value(db_name=db_name, document_id=document_id, field=field)
        elif db_name == "levels":
            if (document := db.levels.find_one({"_id": document_id})) is not None:
                return document[field]
            else:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                Connect.get_field_value(db_name=db_name, document_id=document_id, field=field)

    @staticmethod
    def get_document(db_name: str, document_id: int):
        """Get a whole document with the db_name and id."""
        if db_name == "guilds":
            if (document := db.guilds.find_one({"_id": document_id})) is not None:
                return document
            else:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                Connect.get_document(db_name=db_name, document_id=document_id)
        elif db_name == "users":
            if (document := db.users.find_one({"_id": document_id})) is not None:
                return document
            else:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                Connect.get_document(db_name=db_name, document_id=document_id)
        elif db_name == "levels":
            if (document := db.levels.find_one({"_id": document_id})) is not None:
                return document
            else:
                Connect.generate_document(db_name=db_name, document_id=document_id)
                Connect.get_document(db_name=db_name, document_id=document_id)




