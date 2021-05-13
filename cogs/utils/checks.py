from discord.ext import commands
import logging

log = logging.getLogger()


async def check_role_id(ctx: commands.Context, role_id: int):
    roles = ctx.author.roles

    for role in roles:
        if role.id == role_id:
            return True
    return False


async def check_guild_permissions(ctx: commands.Context, perms: dict, *, check=all):

    resolved = ctx.author.guild_permissions
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


async def is_owner(ctx):
    if ctx.author.id == ctx.bot.owner_id:
        return True
    elif str(ctx.author.id) == ctx.bot.config.owner_id:
        return True
    else:
        return False


async def is_admin(ctx):
    adminrole_id = ctx.bot.mongo_client.db.guilds.find_one({"_id": ctx.guild.id})["adminrole"]
    if await check_guild_permissions(ctx, perms={"administrator": True}):
        return True
    elif await check_role_id(ctx, role_id=adminrole_id):
        return True
    elif await is_owner(ctx) == True:  # bypass for owner
        return True
    else:
        await ctx.error("This is an admin only command.")
        return False


async def is_mod(ctx):
    modrole_id = ctx.bot.mongo_client.db.guilds.find_one({"_id": ctx.guild.id})["modrole"]
    if await check_guild_permissions(ctx, perms={"manage_guild": True}):
        return True
    elif await check_role_id(ctx, role_id=modrole_id):
        return True
    elif await is_admin(ctx):
        return True
    elif await is_owner(ctx):  # again, bypass for owner
        return True
    else:
        await ctx.error("This is a mod only command.")
        return False


async def is_dev(ctx):
    if str(ctx.author.id) in ctx.bot.config.dev_ids:
        return True
    else:
        await ctx.error("This is a dev only command.")
        return False


async def is_nsfw_channel(ctx):
    if ctx.message.guild:
        if ctx.channel.is_nsfw():
            return True
        else:
            await ctx.error("This command is only available in NSFW channels.")
            return False
    else:
        return True
