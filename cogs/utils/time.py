import humanize
import datetime as dt


def convertMilliseconds(milliseconds):
    s = milliseconds / 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{round(h)}:{round(m)}:{round(s)}"


def convertUTCtoHuman(utc):

    return humanize.naturalday(utc)


def getHumanDelta(utc):

    return humanize.naturaldelta(dt.datetime.now() - utc)
