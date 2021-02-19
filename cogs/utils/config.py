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

        self.owner_id = config["IDs"]["OwnerID"] # TODO fix IDs and if satements with IDs
        self.dev_ids = config["IDs"]["DevIDs"]

        self.default_prefix = config["Bot"]["DefaultPrefix"]

        self.ll_host = config["Music"]["LavalinkHost"]
        self.ll_port = config["Music"]["LavalinkPort"]
        self.ll_passwd = config["Music"]["LavalinkPassword"]

        self.enable_redditembed = bool(config["Reddit"]["RedditEmbed"])
        self.praw_username = config["Reddit"]["PrawUsername"]
        self.praw_password = config["Reddit"]["PrawPassword"]
        self.praw_secret = config["Reddit"]["PrawSecret"]
        self.praw_clientid = config["Reddit"]["PrawClientID"]


class GuildConfig:
    def __init__(self, guild):
        if not os.path.exists(f"config/guild/{guild.id}.json"):
            shutil.copyfile(
                "config/example_guild_options.json", f"config/guild/{guild.id}.json"
            )
        with open(f"config/guild/{guild.id}.json") as f:
            guild_config = json.load(f)

        self.automod_newmemberrole = guild_config["AutoMod"]["NewMemberRole"]
        self.automod_greeting = guild_config["AutoMod"]["Greeting"]

        self.guild_modrole = guild_config["Roles"]["ModRole"]
        self.guild_adminrole = guild_config["Roles"]["AdminRole"]

        self.guild_prefix = guild_config["General"]["Prefix"]

class UserConfig:
    def __init__(self, ctx):
        if not os.path.exists(f"config/user/{ctx.author.id}.json"):
            shutil.copyfile(
                "config/example_user_options.json", f"config/user/{ctx.author.id}.json"
            )
        with open(f"config/user/{ctx.author.id}.json") as f:
            user_config = json.load(f)
        
        # TODO all of that