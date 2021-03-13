from discord.ext import commands

class DiscordAPIError(commands.CommandError):
    pass

class UserError(commands.CommandError):
    pass

class TypesNotEqual(commands.CommandError):
    pass

class NoValueGiven(commands.CommandError):
    pass

class GuildConfigError(commands.CommandError):
    pass

class AlreadyConnectedToChannel(commands.CommandError):
    pass

class NoVoiceChannel(commands.CommandError):
    pass

class QueueIsEmpty(commands.CommandError):
    pass

class NoTracksFound(commands.CommandError):
    pass

class PlayerIsAlreadyPaused(commands.CommandError):
    pass

class PlayerIsNotPaused(commands.CommandError):
    pass

class NoMoreTracks(commands.CommandError):
    pass

class NoPreviousTracks(commands.CommandError):
    pass

class InvalidRepeatMode(commands.CommandError):
    pass

class InvalidQueueEntry(commands.CommandError):
    pass

class InvalidQueuePosition(commands.CommandError):
    pass

class QueryError(commands.CommandError):
    pass

class TrackNotFound(commands.CommandError):
    pass

class ProbablyInvalidSpotifyLink(commands.CommandError):
    pass

class NoResultsFound(commands.CommandError):
    pass

class MongoError(Exception):
    pass

class APIError(commands.CommandError):
    pass

