# Copyright (c) 2015 noteness
# Copyright (c) 2011 Duncan Fordyce, Jimmy Cao
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
from __future__ import print_function,division
import socket
import ssl
import sys
import threading
import time
import datetime
import irc
import traceback
from parse import *
import os
import base64
import src
argsa=src.args
date = str(datetime.date.today())

class TokenBucket(object):
    """An implementation of the token bucket algorithm.

    >>> bucket = TokenBucket(80, 0.5)
    >>> bucket.consume(1)
    """
    def __init__(self, tokens, fill_rate):
        """tokens is the total tokens in the bucket. fill_rate is the
        rate in tokens/second that the bucket will be refilled."""
        self.capacity = float(tokens)
        self._tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.time()

    def consume(self, tokens):
        """Consume tokens from the bucket. Returns True if there were
        sufficient tokens otherwise False."""
        if tokens <= self.tokens:
            self._tokens -= tokens
            return True
        return False

    @property
    def tokens(self):
        now = time.time()
        if self._tokens < self.capacity:
            delta = self.fill_rate * (now - self.timestamp)
            self._tokens = min(self.capacity, self._tokens + delta)
        self.timestamp = now
        return self._tokens


def add_commands(d):
    def dec(cls):
        for c in d:
            def func(x):
                def gen(self, *a):
                    self.send(x.upper()+" "+" ".join(a))
                return gen
            setattr(cls, c, func(c))
        return cls
    return dec
@add_commands(("join",
               "mode",
               "nick",
               "who",
               "cap",
               "part",
               "znc",
               "cs",
               "ns",
               "topic"))
class bot(object):
    def __init__(self,cmd_handler,**args):
        self.command_handler = cmd_handler
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mserver="irc.freenode.net"
        self.botnick = "Slavetator"
        self.addrchar="^"
        self.ownercloak=[]
        self.account = ""
        self.password = ""
        self.port = 6697
        self.server_password=""
        self.lock = threading.RLock()
        self.needssl = True
        self.channels= ["#Slavetator"]
        self.debugchannel="#Slavetator-test"
        self.handler= lambda text,level=None : print(text)
        self.tokenbucket = TokenBucket(23, 1.73)
        self.znc= False
        self.admin_nicks= []
        self.admin_accounts = []
        self.sasl=False
        self.ident=self.botnick
        self.hostmask=self.botnick
        self.realname = self.botnick
        socket.setdefaulttimeout(120) 
        self.thread= threading.Thread(target=self.pinger)
        self.thread.daemon=True
        self.connect_cb = None
        self.devchan = "#Slavetator-dev"
        self.main_chan= "#Slavetator"
        self.__dict__.update(args)
        if self.needssl:
            self.socket = ssl.wrap_socket(self.socket,do_handshake_on_connect=True)
        self._end = 0
        if argsa.debug:
            self.channels=set(list(self.debugchannel))
        self.channels.add(self.devchan)
        self.jchannels = ",".join(self.channels)
    def msg(self, user, msg):
        msg = str(msg)

        for line in msg.split('\n'):
            maxchars = 494 - len(self.botnick+self.ident+self.hostmask+user)
            while line:
                extra = ""
                if len(line) > maxchars:
                    extra = line[maxchars:]
                    line = line[:maxchars]
                self.send("PRIVMSG", user, ":{0}".format(line))
                line = extra
    privmsg = msg  # Same thing
    def quit(self,msg="I am not a BOT!"):
        if self.socket:
            try:
                self.send("QUIT :{0}".format(msg))
                time.sleep(5)
            except:
                pass
            raise SystemExit
    def notice(self, user, msg):
        msg = str(msg)
        for line in msg.split('\n'):
            maxchars = 495 - len(self.botnick+self.ident+self.hostmask+user)
            while line:
                extra = ""
                if len(line) > maxchars:
                    extra = line[maxchars:]
                    line = line[:maxchars]
                self.send("NOTICE", user, ":{0}".format(line))
                line = extra
    def whox(self,chan):
        self.send("WHO "+chan+" %tna,08")
    def on_whox(self,rest):
        if rest.split(' ') [0] == "08":
            resty=rest.split(' ')
            a_nick= resty [1]
            account = resty [2]
 
            if account in self.admin_accounts:
                if not a_nick in self.admin_nicks:
                    self.admin_nicks.append(a_nick)
                    self.handler("Added {0} to admins".format(a_nick))
            else:
                self.handler("{0} Not in Admins".format(a_nick))
    def restart(self,msg="Restarting..."):

        try:
            self.quit(msg=msg)

        except:
            pass
        self.handler("Restarting....",level="warning")
        execut = sys.executable
        os.execl(execut, execut, *sys.argv)
    def pinger(self):
        while True:
            time.sleep(100)
            self.send("PING "+str(int(time.time())))
    def pong(self,msg):
        pong= msg.lower().replace("ping",'PONG')
        self.send(pong)
    def send(self,*msg):
        with self.lock:
            msg = " ".join(msg)
            while not self.tokenbucket.consume(1):
                time.sleep(0.3)

            self.socket.send(msg+"\n")
            self.handler ("---> send "+msg)
            while not self.tokenbucket.consume(1):
                time.sleep(0.3)

    def recvmsg(self,msg):
            self.handler ("<--- "+msg)
    def connect(self):
        try:
            buffer = ""
            self.handler('***Start Logging on ' + date +'***')
            retries = 0
            
            while True:
                try:
                    self.handler('Starting Bot...',level="warning")
                    self.handler('Connecting to {0}  Port {1}'.format(self.mserver,str(self.port)),level="warning")
                    self.socket.connect(("{0}".format(self.mserver), self.port))
                    self.handler('Connected!',level="warning")
                    break
                except socket.error as e:
                    retries += 1
                    self.handler('Error: {0}'.format(e),level="warning")
                    if retries > 3:
                        self.handler('Connection failed after 3 retires.',level="warning")
                        self._end= True
                        break
            self.cap("LS","302")
            if self.server_password:
                self.send("PASS {0}".format(self.server_password))
            self.send(str(('NICK '+self.botnick)))
            self.send(" ".join(("USER", self.ident, self.mserver, self.mserver, ":{0}".format(self.realname or self.ident))))
            if self.connect_cb:
                try:
                    self.connect_cb(self)
                except Exception as e:
                    traceback.print_exc()
                    raise e
            self.handler('Connected!',level="warning")
            self.thread.start()
            while not self._end:
                    try:
                        buffer += self.socket.recv(1024)
                        data= buffer.split('\n')
                        buffer= data.pop()
                        for x in data:
                            prefix, command, args = parse_raw_irc_command(x)
                            try:
                                largs = list(args)
                                fargs = [arg.decode('utf_8') for arg in args]
                                self.handler(u"<--- receive {0} {1} ({2})".format(prefix, command, ", ".join(fargs)), level="debug")
                                # for i,arg in enumerate(largs):
                                    # if arg is not None: largs[i] = arg.decode(enc)
                                if command in self.command_handler:
                                    self.command_handler[command](self, prefix,*fargs)
                                elif "" in self.command_handler:
                                    self.command_handler[""](self, prefix, command, *fargs)
                            
                            except Exception as e:
                                traceback.print_exc()
                                raise e  # ?
                    except socket.timeout:
                        self.handler('socket timeout') 
                        self.restart()

                    except socket.error as e:
                        if False and not self.blocking and e.errno == 11:
                            pass
                        else:
                            self.handler(e,level="warning")
                            raise
                    except:
                        raise

                    yield True
        except:
            traceback_exception_yy=traceback.format_exc()
            if argsa.debug:
                self.handler("Detailed Exception info:\n"+traceback_exception_yy,level="warning")
            else:
                abcd =str(sys.exc_info()[0])
                abcd = "Exception: "+abcd.strip("<type 'exceptions.").strip("'>")
                self.handler(abcd)
            raise 

        finally:
                if self.socket:
                    try:
                        self.send("QUIT :Sayonara")
                        self.socket.close()
                    except:
                        pass

                yield False
    def MainLoop(self):
        conn = self.connect()
        while True:
            if not next(conn):
                self.handler("Calling sys.exit.....",level="warning")
                sys.exit()
    def ctcpreply(self,nick,ctcp,reply):
        self.notice(nick,'\x01{0} {1}\x01'.format(ctcp,reply))