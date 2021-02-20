from discord.ext import commands
import logging

log = logging.getLogger()

async def check_guild_permissions(ctx, perms, *, check=all):

    resolved = ctx.author.guild_permissions
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


async def is_owner(ctx):
    if ctx.bot.config.owner_id == "auto" and ctx.author.id == ctx.bot.owner_id:
        return True
    elif str(ctx.author.id) == ctx.bot.config.owner_id:
        return True
    else:
        return False


async def is_admin(ctx):
    if await check_guild_permissions(ctx, {"administrator": True}):
        return True
    elif is_owner(ctx) == True:  # bypass for owner
        return True
    else:
        await ctx.error("This is an admin only command.")
        return False


async def is_mod(ctx):
    if await check_guild_permissions(ctx, {"manage_guild": True}):
        return True
    elif is_admin(ctx):
        return True
    elif is_owner(ctx):  # again, bypass for owner
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
