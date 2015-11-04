# Copyright (c) 2015 noteness
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import irc.parse as parser

#from usercontrol import *
import decorators
import config
import re
import time
import src
import os
import binascii
from bs4 import BeautifulSoup
import urllib2
COMMANDS = decorators.COMMANDS
ctcp = decorators.ctcps
hook = decorators.hook
cmd= decorators.cmd
def break_long_message(phrases, joinstr = " "):
    message = []
    count = 0
    for phrase in phrases:
        # IRC max is 512, but freenode splits around 380ish, make 300 to have plenty of wiggle room
        if count + len(joinstr) + len(phrase) > 300:
            message.append("\n" + phrase)
            count = len(phrase)
        else:
            if message:
                count = len(phrase)
            else:
                count += len(joinstr) + len(phrase)
            message.append(phrase)
    return joinstr.join(message)

CMD_CHAR = config.ADDRCHAR
@cmd("help", raw_nick=True, pm=True)
def get_help(cli, rnick, chan, rest):
    """Gets help."""
    nick, mode, user, cloak = parser.parse_nick(rnick)
    fns = []

    rest = rest.strip().replace(CMD_CHAR, "", 1).lower()
    splitted = re.split(" +", rest, 1)
    cname = splitted.pop(0)
    rest = splitted[0] if splitted else ""
    if cname:
        if cname in COMMANDS.keys():
            for fn in COMMANDS[cname]:
                if fn.__doc__:
                    got = True
                    if callable(fn.__doc__):
                        msg = CMD_CHAR+cname+": "+fn.__doc__(rest)
                    else:
                        msg = CMD_CHAR+cname+": "+fn.__doc__
                    if chan == nick:
                        cli.msg( nick, msg)
                    else:
                        cli.notice(nick, msg)
                    return
                else:
                    got = False
                    continue
            else:
                if got:
                    return
                elif chan == nick:
                    cli.msg(nick, "Documentation for this command is not available.")
                else:
                    cli.notice(nick, "Documentation for this command is not available.")

        elif chan == nick:
            cli.msg(nick, "Command not found.")
        else:
            cli.notice(nick, "Command not found.")
        return

    # if command was not found, or if no command was given:
    for name,fn in COMMANDS.items():
        if name == '':
            continue
        if (name and not fn[0].admin_only and
            name not in fn[0].aliases and fn[0].chan):
            fns.append("{0}{1}{0}".format(u"\u0002", name))
    afns = []
    if (nick in cli.admin_nicks) or (cloak in cli.ownercloak):
        for name, fn in COMMANDS.items():
            if name == '':
                continue
            if fn[0].admin_only and name not in fn[0].aliases:
                afns.append("{0}{1}{0}".format(u"\u0002", name))
    fns.sort() # Output commands in alphabetical order
    if chan == nick:
        cli.msg(nick, "Available Commands: {0}".format(break_long_message(fns, ", ")))
    else:
        cli.notice(nick, "Available Commands: {0}".format(break_long_message(fns, ", ")))
    if afns:
        afns.sort()
        if chan == nick:
            cli.msg(nick, "Admin Commands: {0}".format(break_long_message(afns, ", ")))
        else:
            cli.notice(nick, "Admin Commands: {0}".format(break_long_message(afns, ", ")))

@cmd("opme","opame", admin_only=True,pm=False)
def opme(cli, nick, chan, rest):
    """Ops You"""
    cli.mode(chan,"+o",nick)
    cli.cs("OP",chan,nick)
    return
@cmd("op", admin_only=True,pm=False)
def op(cli, nick, chan, rest):
    """Ops the nick specified or ops the bot if none"""
    if rest:
        cli.mode(chan,"+o",rest)
        cli.cs("OP",chan,rest)
    else:
        cli.cs("OP",chan,cli.botnick)

@cmd("topic", admin_only=True,pm=False)
def topic(cli, nick, chan, rest):
    """Changes the topic of the channel"""
    cli.topic(chan,':'+rest)
@cmd("restart", admin_only=True,pm=True)
def restart(cli, nick, chan, rest):
    """Restarts the bot"""
    cli.restart(msg="Forced restart by {0}".format(nick))
@cmd("exec", admin_only=True,pm=True)
def exe(cli, nick, chan, rest):
    """Executes the given code"""
    exec(rest)
@cmd("eval", admin_only=True,pm=True)
def ev(cli, nick, chan, rest):
    """Evaluates the code and give you the results"""
    evaluated = eval(rest)
    if chan == nick:
        cli.msg(nick,evaluated)
    else:
        cli.notice(nick,evaluated)
@cmd("quit","bye", admin_only=True,pm=True)
def restart(cli, nick, chan, rest):
    """Makes the bot quit IRC"""
    cli.quit(msg="Forced quit by {0}".format(nick))
@cmd("send", admin_only=True,pm=True)
def send(cli, nick, chan, rest):
    """Sends Raw IRC lines"""
    cli.send(rest)
@cmd("reload", admin_only=True,pm=True)
def send(cli, nick, chan, rest):
    """Reloads the commands module"""
    rreload(bot)
    if chan == nick:
        cli.msg(nick,"The operation succeeded")
    else:
        cli.notice(nick,"The operation succeeded")
@cmd("version","info",pm=True)
def bt_info(cli, nick, chan, rest):
    """Shows information about the bot"""
    cli.msg(chan,"{0}: I am a basic server handling bot running purely on Python. \nYou can visit my website - http://slavetator.github.io/ :)\nSee any bugs? report it by {1}bug <description>".format(nick,CMD_CHAR))
@cmd("bug",pm=True)
def bt_info(cli, nick, chan, rest):
    """Report bugs"""
    import datetime
    timed = "[{0}]".format(datetime.datetime.now())
    with open('logs/bugs.txt','a') as bugf:
        bugf.write("{0} BUG: Reported by: {1} Description: {2}\r\n".format(timed,nick,rest))
    cli.msg('noteness','\x02!att-slavetator-bug\x02 Reported by: \x02{0}\x02 Description: \x02{1}\x02'.format(nick,rest))
    if chan == nick:
        cli.msg(nick,"The operation succeeded\nThank you for your contribution :)")
    else:
        cli.notice(nick,"The operation succeeded\nThank you for your contribution :)")
@ctcp('version')
def ctcp_ver(cli,chan,nick):
    cli.ctcpreply(nick,'VERSION',"Slavetator - http://slavetator.github.io/")
@ctcp('time')
def ctcp_ver(cli,chan,nick):
    cli.ctcpreply(nick,'TIME',"It's Tea O'Clock")

cycle = 0
@hook("ping")
def on_ping(cli, prefix, server):
    cli.send('PONG', server)
@hook("nicknameinuse")
def nickinuse(cli, *blah):
    cli.botnick += "_"
    cli.nick(cli.botnick)
@hook("pong")
def on_pong(cli, prefix, server,timet):
    global cycle
    if timet.isdigit():
        lag = int(time.time()) - int(timet)
        if lag > 3:
            cycle +=1
            cli.msg(cli.main_chan,"\x02Warning:\x02 I am lagging by \x02{0}\x02 seconds.\nThis marks heavy lag cycle \x02{1}.\x02 Automatic restart will initiate at \x023\x02 lag cycles".format(lag,cycle))
        else:
            cycle = 0
        if cycle > 2:
            cli.restart(msg="Restarting due to heavy lag cycles")
@cmd("join",admin_only=True,pm=True)
def fjoin(cli,nick,chan,rest):
    """Makes the bot join a channel"""
    cli.join(rest)
    if "," in rest:
        rest = rest.split(',')
    if not src.args.debug:
        if isinstance(rest,list):
            for ech in rest:
                config.CHANNELS.append(rest)
        else:
            config.CHANNELS.append(rest)
    if chan == nick:
        cli.msg(nick,"The operation succeeded")
    else:
        cli.notice(nick,"The operation succeeded")
@cmd("part","leave",admin_only=True,pm=True)
def fjoin(cli,nick,chan,rest):
    """Makes the bot part a channel"""
    cli.part(rest)
    if "," in rest:
        rest = rest.split(',')
    if not src.args.debug:
        if isinstance(rest,list):
            for ech in rest:
                if rest in config.CHANNELS:
                    config.CHANNELS.remove(rest)
        else:
            if rest in config.CHANNELS:
                config.CHANNELS.remove(rest)
    if chan == nick:
        cli.msg(nick,"The operation succeeded")
    else:
        cli.notice(nick,"The operation succeeded")
@cmd("flush","savecfg",admin_only=True,pm=True)
def flush(cli,nick,chan,rest):
    """Write the config to disk"""
    from src import atexits
    atexits.saveconf()
    if chan == nick:
        cli.msg(nick,"The operation succeeded")
    else:
        cli.notice(nick,"The operation succeeded")


def rreload(module):
    """Recursively reload modules."""
    from types import ModuleType
    reload(module)
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if type(attribute) is ModuleType:
            rreload(attribute)
@cmd("bash")
def bashorg(cli,nick,chan,rest):
    """Gets quotes from bash.org"""

    req = urllib2.Request('http://bash.org?random1')
    response = urllib2.urlopen(req)
    the_page = response.read()
    soup = BeautifulSoup(the_page)
    raw = soup.find(class_="qt")
    lines = raw.get_text().splitlines()
    lines = '\n'.join(lines)
    cli.msg(chan,lines)


