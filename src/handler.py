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

from __future__ import absolute_import
# The bot commands implemented in here are present no matter which module is loaded

import base64
import imp
import socket
import traceback
import threading
from irc.parse import parse_nick
import time
from src import decorators, logging,commands
import config
log = logging("logs/errors.log").log
alog = logging(None).log
locky = threading.RLock()
hook = decorators.hook

def notify_error(cli, chan, target_logger,ctcp=False):
	if ctcp:
		msg = "An error has occurred while processing a ctcp request and has been logged."
	else:
		msg = "An error has occurred and has been logged."

	tb = traceback.format_exc()

	target_logger(tb)
	with locky:
		try:
		
			sock = socket.socket()
			sock.connect(("termbin.com", 9999))
			sock.send(tb.encode("utf-8", "replace") + b"\n")
			url = sock.recv(1024).decode("utf-8")
			sock.close()
		except socket.error:
			target_logger(traceback.format_exc())
		else:
			cli.msg(cli.devchan, " ".join((msg, url)))
		if chan != cli.devchan:
			cli.msg(chan,msg)

	


def on_privmsg(cli, rawnick, chan, msg, notice = False):


	if chan == config.NICK:
		chan = parse_nick(rawnick)[0]

	for fn in decorators.COMMANDS[""]:
		try:
			fn.caller(cli, rawnick, chan, msg)
		except Exception:
			notify_error(cli,chan,log)



	for x in decorators.COMMANDS:
		if chan != parse_nick(rawnick)[0] and not msg.lower().startswith(config.ADDRCHAR):
			break # channel message but no prefix; ignore
		if msg.lower().startswith(config.ADDRCHAR+x):
			h = msg[len(x)+len(config.ADDRCHAR):]
		elif not x or msg.lower().startswith(x):
			h = msg[len(x):]
		else:
			continue
		if not h or h[0] == " ":
			for fn in decorators.COMMANDS.get(x, []):
				try:
					fn.caller(cli, rawnick, chan, h.lstrip())
				except Exception:
					notify_error(cli,chan,log)

def on_ctcp(cli,prefix,chan,ctcp):
	ctcp = ctcp.lower()
	if ctcp in decorators.CTCP:
		for fn in decorators.CTCP.get(ctcp, []):
			try:
				fn.caller(cli, prefix, chan)
			except Exception:
				notify_error(cli,cli.devchan,log,ctcp=True)

def unhandled(cli, prefix, cmd, *args):

	if cmd in decorators.HOOKS:
		largs = list(args)
		for i,arg in enumerate(largs):
			if isinstance(arg, bytes): largs[i] = arg.decode('ascii')
		for fn in decorators.HOOKS.get(cmd, []):
			try:
				fn.func(cli, prefix, *largs)
			except Exception:
				notify_error(cli,cli.devchan,log)


def connect_callback(cli):
	@hook("endofmotd", hookid=294)
	@hook("nomotd", hookid=294)
	def prepare_stuff(cli, *args):
		# just in case we haven't managed to successfully auth yet
		if not cli.sasl:
			cli.send("NICKSERV :identify",cli.account,cli.password)

		channels = ",".join(cli.channels)
		cli.join(channels)
		cli.nick(cli.botnick)  # very important (for regain/release)
		cli.nick(cli.botnick)
		hook.unhook(294)
	@hook("unavailresource", hookid=239)
	@hook("nicknameinuse", hookid=239)
	def must_use_temp_nick(cli, *etc):
		cli.send("NICK {0}_".format(cli.botnick))
		cli.botnick = cli.botnick+"_"

		hook.unhook(239)


	request_caps = {"account-notify", "extended-join", "multi-prefix"}

	if config.USE_SASL:
		request_caps.add("sasl")

	supported_caps = set()


	@hook("cap")
	def on_cap(cli, svr, mynick, cmd, caps, star=None):
		if cmd == "LS":
			if caps == "*":
				# Multi-line LS
				supported_caps.update(star.split())
			else:
				supported_caps.update(caps.split())

				if cli.sasl and "sasl" not in supported_caps:
					alog("Server does not support SASL authentication")
					cli.quit()

				common_caps = request_caps & supported_caps

				if common_caps:
					cli.cap("REQ", ":{0}".format(" ".join(common_caps)))
		elif cmd == "ACK":
			if "sasl" in caps:
				cli.send("AUTHENTICATE PLAIN")
			else:
				cli.cap("END")
		elif cmd == "NAK":
			# This isn't supposed to happen. The server claimed to support a
			# capability but now claims otherwise.
			alog("Server refused capabilities: {0}".format(" ".join(caps)))


	if cli.sasl:
		@hook("authenticate")
		def auth_plus(cli, something, plus):
			if plus == "+":
				account = cli.account.encode("utf-8")
				password = cli.password.encode("utf-8")
				auth_token = base64.b64encode(b"\0".join((account, account, password))).decode("utf-8")
				cli.send("AUTHENTICATE " + auth_token)

		@hook("saslsuccess")
		def on_successful_auth(cli, blah, blahh, blahhh):
			cli.cap("END")

		@hook("saslfail")
		@hook("sasltoolong")
		@hook("saslaborted")
		@hook("saslalready")
		def on_failure_auth(cli, *etc):
			alog("Authentification failed.\nIs everything ok?")
			cli.quit()




# vim: set expandtab:sw=4:ts=4:
