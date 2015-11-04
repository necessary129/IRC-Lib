#!/usr/bin/env python
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
import os
import atexit
import os.path
import sys

if not os.path.isfile("config.py"):
   import shutil
   print "Copying config.py.example to config.py"
   shutil.copy("config.py.example", "config.py")
import config
if not config.configured:
   print "You haven't configured. Exiting now....."
   sys.exit(1)
from irc.client import bot

import src
import sys
import src.handler as handler
import src.atexits as atexits
py_version = sys.version_info
major = int(py_version [0])
minor = int(py_version [1])
if major < 3 and major > 1:
   if minor < 7:
      print 'Python 2.7 is required to run the bot.'
      sys.exit(1)
else:
   print 'Bot can be only ran in Python 2.7.'
   sys.exit(1)
def main():
   cli=bot(
      {"privmsg": handler.on_privmsg,
       "ctcp": handler.on_ctcp,
       "notice": lambda a, b, c, d: handler.on_privmsg(a, b, c, d, True),
       "": handler.unhandled},
      botnick=config.NICK,
      account=config.USERNAME,
      username = config.USERNAME,
      password=config.PASSWORD,
      mserver=config.SERVER,
      channels=config.CHANNELS,
      addrchar=config.ADDRCHAR,
      ownercloak=config.ADMIN_CLOAKS,
      port=config.PORT,
      sasl=config.USE_SASL,
      debugchannel=config.DEBUG_CHANNEL,
      server_password=config.SERVER_PASSWORD,
      znc=config.USING_ZNC,
      admin_accounts=config.ADMIN_ACCOUNTS,
      handler=src.printer,
      needssl=config.SSL,
      connect_cb=handler.connect_callback,
      )
   cli.MainLoop()

if __name__ == '__main__':
   main()
