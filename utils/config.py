import logging
import os
import shutil
import json
import codecs
from configparser import ConfigParser


# TODO maybe add a fallback, in case the user forgets to set a setting
class Config:
    def __init__(self):
        config = ConfigParser()
        if not os.path.exists("config/options.ini"):
            shutil.copyfile("config/example_options.ini", "config/options.ini")
        with open("config/options.ini") as f:
            config.read_file(f)

        self.login_token = config["Credentials"]["Token"]
        self.client_id = config["Credentials"]["ClientID"]
        self.mongodb_url = config["Credentials"]["MongoDBUrl"]
        self.saucenao_api = config["Credentials"]["SaucenaoAPIKey"]

        self.owner_id = config["IDs"]["OwnerID"]  # TODO fix IDs and if satements with IDs
        self.dev_ids = config["IDs"]["DevIDs"]

        self.default_prefix = config["Bot"]["DefaultPrefix"]

        self.ll_host = config["Music"]["LavalinkHost"]
        self.ll_port = config["Music"]["LavalinkPort"]
        self.ll_passwd = config["Music"]["LavalinkPassword"]
        self.spotify_client_id = config["Music"]["SpotifyClientID"]
        self.spotify_client_secret = config["Music"]["SpotifyClientSecret"]

        self.praw_username = config["Reddit"]["PrawUsername"]
        self.praw_password = config["Reddit"]["PrawPassword"]
        self.praw_secret = config["Reddit"]["PrawSecret"]
        self.praw_clientid = config["Reddit"]["PrawClientID"]
