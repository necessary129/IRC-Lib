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
# THE SOFTWARE
import numerics 
import re
numert = numerics.numerics
import config
#addrchar= config.ADDRCHAR
def parse_privmsg(msg):
    try:
        splitt = msg.split('!') 
        nick = splitt [0] [1:]
    except IndexError:
        return (msg,None,None,None,None,None)
    try:
        splitt= splitt [1].split('@',1)
        ident = splitt [0]
    except IndexError:
        return (nick,msg,None,None,None,None)
    try:
        splitt= splitt [1].split(' ',3)
        cloak = splitt [0]
    except IndexError:
        return (nick,ident,msg,None,None,None)
    try:
        channel = splitt [2]
        
        (nick,ident,cloak,channel,None,None)
    except IndexError:
        return (nick,ident,cloak,None,None,None)
    try:
        message = splitt [3].lstrip(':')
        if message [0] == addrchar:
            message=message.lstrip(addrchar)
            try:
                splittedmsg = message.split(' ',1)
                command = splittedmsg [0]
                rest = splittedmsg [1]
                return (nick,ident,cloak,channel,command,rest)
            except IndexError:
                return (nick,ident,cloak,channel,command,None)
        else:
            return (nick,ident,cloak,channel,message,None,None)
    except IndexError:
        return (nick,ident,cloak,channel,None,None,None)
def parse_raw_with_numeric(msg):
    splitted=msg.split(' ',3)
    number_got=splitted [1]
    rest=splitted [3]
    numeric=numert[number_got] 

    return (numeric,rest)
def parse_numeric(msg):
    splitted=msg.split(' ')
    number=splitted [1]
    return numert[number] 

def parse_nick(name):
    """ parse a nickname and return a tuple of (nick, mode, user, host)

    <nick> [ '!' [<mode> = ] <user> ] [ '@' <host> ]
    """

    try:
        nick, rest = name.split('!')
    except ValueError:
        return (name, None, None, None)
    try:
        mode, rest = rest.split('=')
    except ValueError:
        mode, rest = None, rest
    try:
        user, host = rest.split('@')
    except ValueError:
        return (nick, mode, rest, None)

    return (nick, mode, user, host)


def parse_raw_irc_command(element):
    """
    This function parses a raw irc command and returns a tuple
    of (prefix, command, args).
    The following is a psuedo BNF of the input text:

    <message>  ::= [':' <prefix> <SPACE> ] <command> <params> <crlf>
    <prefix>   ::= <servername> | <nick> [ '!' <user> ] [ '@' <host> ]
    <command>  ::= <letter> { <letter> } | <number> <number> <number>
    <SPACE>    ::= ' ' { ' ' }
    <params>   ::= <SPACE> [ ':' <trailing> | <middle> <params> ]

    <middle>   ::= <Any *non-empty* sequence of octets not including SPACE
                   or NUL or CR or LF, the first of which may not be ':'>
    <trailing> ::= <Any, possibly *empty*, sequence of octets not including
                     NUL or CR or LF>

    <crlf>     ::= CR LF
    """
    parts = element.strip().split(" ")
    if parts[0].startswith(':'):
        prefix = parts[0][1:]
        command = parts[1]
        args = parts[2:]
    else:
        prefix = None
        command = parts[0]
        args = parts[1:]

    if command.isdigit():
        try:
            command = numert[command]
        except KeyError:
            pass
    command = command.lower()

    if args[0].startswith(':'):
        args = [" ".join(args)[1:]]
    else:
        for idx, arg in enumerate(args):
            if arg.startswith(':'):
                args = args[:idx] + [" ".join(args[idx:])[1:]]
                break
    result = re.search('\x01(.+)\x01',element)
    if result:
        if command == 'privmsg':
            command = 'ctcp'
        elif command == 'notice':
            command = 'ctcpreply'
        args[-1] = result.group(1)
    return (prefix, command, args)

