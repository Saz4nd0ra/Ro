# Ro-discord-bot

A bot made for servers that I like! 

### Before we start

You can setup your own instance of ADB, yet you should consider inviting the already hosted instance to your server. 
If you want to host it yourself, go ahead and read through the instructions.


## Installation

These are the instructions to install Lavalink and the bot itself. The bot is written with Linux in mind,
so Windows support isn't confirmed. Any major distro should work, these instructions are written using Arch.

### Installation: Lavalink

1. **Install Java 15.**

Please look this up, since that process is different for each OS. The bot was tested with `jdk-openjdk` on Arch Linux and AdoptOpenJDK on Windows. Both times with the version 15. So as long as you install that specific JDK on your distro/OS you should be fine. 

### Installation: Python & Venv

1. **Checking the version of Python**

Some distros come with Python 3.7 or 3.8 preinstalled. You can check the version with either `python --version` or `python3 --version`.
If one of the commands gave the output or `Python 3.7.x` or `Python 3.8.x` you can skip the installation of Python. 

2. **Installing Python**

Again, look this up on the internet. We will need a virtual env for the bot, which you might need to install seperataley, this is especially the case on Debian based distros, again, look that up for your specific Distro. So look that up as well.

### Installation: Requirements

1. **Install requirements**

First you need to activate the venv with `source /venv/bin/activate`.
You are now using the venv, well done. You might need to install wheel using `pip install wheel`,
after that is finished, install the requirements with `pip install -r requirements.txt`, this could take a while.

You finished the installation, now you can go ahead and set everything up.

## Setup

### MongoDB configuration

TODO

### Bot configuration

**Setup configuration**

Change these settings in the `config/options.ini` to make the bot work. If the file doesn't exist, start the bot once to generate it.

```ini
[Credentials]

Token = ...

ClientID =

[Audio]

LavalinkHost = ...
LavalinkPort = ...
LavalinkPassword = ...
```

## Other stuff

TODO
