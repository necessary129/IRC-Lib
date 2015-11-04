# Copyright (c) 2015 noteness
# Copyright (c) 2015 lykos development team
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

import fnmatch
from collections import defaultdict
import irc.parse as parser
from src import logging as logg
import datetime
parse_nick = parser.parse_nick
COMMANDS = defaultdict(list)
HOOKS = defaultdict(list)
CTCP = defaultdict(list)
adminlog= logg('logs/audits.log',display=False).log
class cmd:
    def __init__(self,*cmds,**args):
        self.cmds = cmds
        self.raw_nick = False
        self.admin_only = False
        self.chan = True
        self.pm = False
        self.func = None
        self.name = cmds[0]
        self.__dict__.update(args)
        alias = False
        self.aliases = []
        for name in cmds:
            for func in COMMANDS[name]:
                if (func.owner_only != owner_only or
                    func.admin_only != admin_only):
                    raise ValueError("unmatching protection levels for " + func.name)

            COMMANDS[name].append(self)


            if alias:
                self.aliases.append(name)
            alias = True

    def __call__(self, func):
        self.func = func
        self.__doc__ = self.func.__doc__
        return self

    def caller(self, *args):
        largs = list(args)

        cli, rawnick, chan, rest = largs
        nick, mode, user, cloak = parse_nick(rawnick)

        if cloak is None:
            cloak = ""

        if not self.raw_nick:
            largs[1] = nick

        if not self.pm and chan == nick:
            return # PM command, not allowed

        if not self.chan and chan != nick:
            return # channel command, not allowed

        if chan.startswith("#") and chan != cli.channels and not (self.admin_only):
            if "" in self.cmds:
                return # don't have empty commands triggering in other channels


        if "" in self.cmds:
            return self.func(*largs)
    

        if nick in cli.admin_nicks or cloak in cli.ownercloak:
            if self.admin_only:
                adminlog("[{0}]".format(datetime.datetime.now()),rawnick,"Used Command:",self.name,rest,"On:",chan)
            return self.func(*largs)


        if self.admin_only:
            if chan == nick:
                cli.msg(nick, "You are not an admin.")
            else:
                cli.notice(nick, "You are not an admin.")
            return

        return self.func(*largs)

class ctcps:
    def __init__(self,ctcp):
        self.ctcp = ctcp
        self.func = None
        CTCP[ctcp].append(self)
    def __call__(self,func):
        self.func = func
        self.__doc__ = self.func.__doc__
        return self
    def caller(self,cli,rnick,chan):
        nick, mode, user, cloak = parse_nick(rnick)
        return self.func(cli,chan,nick)

class hook:
    def __init__(self, name, hookid=-1):
        self.name = name
        self.hookid = hookid
        self.func = None

        HOOKS[name].append(self)

    def __call__(self, func):
        if isinstance(func, hook):
            self.func = func.func
        else:
            self.func = func
        self.__doc__ = self.func.__doc__
        return self

    @staticmethod
    def unhook(hookid):
        for each in list(HOOKS):
            for inner in list(HOOKS[each]):
                if inner.hookid == hookid:
                    HOOKS[each].remove(inner)
            if not HOOKS[each]:
                del HOOKS[each]