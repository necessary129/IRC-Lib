from __future__ import print_function
from __future__ import unicode_literals
#import dbcontrol
import io
import os
import argparse
import datetime
if not os.path.exists("logs/"):
    os.mkdir('logs/')
parser = argparse.ArgumentParser(description='More controls.')
parser.add_argument('-v','--verbose',  action='store_true',
                    default=False,
                    help='more verbosity, prints everything.')
parser.add_argument('-d','--debug',  action='store_true',
                    default=False,
                    help='Run in debug mode.')
args = parser.parse_args()
utf8stdout = io.open(1, 'w',encoding='utf_8', errors="replace", closefd=False)
#dbcontrol.check_db()
class logging(object):
    def __init__(self,file,write=True,display=True):
        self.file=file
        self.write=write
        self.display=display
    def log(self,*output):
        abcd=[]
        for x in output:
            if not x:
                continue
            x=unicode(x,encoding='utf_8',errors='replace') if not isinstance(x,unicode) else x
            abcd.append(x)
        output = " ".join(abcd)
        if args.debug:
            self.write = True
        if args.verbose or args.debug:
            self.display = True

        if self.display:
            print(output, file=utf8stdout)
        if self.write and self.file is not None:
            with io.open(self.file, "a",encoding='utf_8', errors="replace") as f:
                f.seek(0, 2)
                f.write(output + "\n")

logger = logging('logs/debug.log',display=False,write=False).log
shandler = logging(None).log


def printer(Text,level=None):
        Text=unicode(str(Text),encoding='utf_8',errors='replace') if not isinstance(Text,unicode) else Text

        time= unicode(str(datetime.datetime.now()),encoding='utf_8',errors='replace')
        ttext ="["+time+"] "+Text
        if Text.startswith('***'):
            logger(Text)
            return
        else:
            if level == "warning" and (not Text.startswith('***')) and not (args.verbose or args.debug):
                shandler(ttext)
            logger(ttext if not Text.startswith('***') else Text)

