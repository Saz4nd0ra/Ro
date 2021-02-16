import logging
import os
import shutil
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

        self.owner_id = config["IDs"]["OwnerID"]
        self.dev_ids = config["IDs"]["DevIDs"]

        self.prefix = config["Bot"]["DefaultPrefix"]

        self.ll_host = config["Music"]["LavalinkHost"]
        self.ll_port = config["Music"]["LavalinkPort"]
        self.ll_passwd = config["Music"]["LavalinkPassword"]

        self.enable_redditembed = config["Reddit"]["RedditEmbed"]
        self.praw_username = config["Reddit"]["PrawUsername"]
        self.praw_password = config["Reddit"]["PrawPassword"]
        self.praw_secret = config["Reddit"]["PrawSecret"]
        self.praw_clientid = config["Reddit"]["PrawClientID"]
