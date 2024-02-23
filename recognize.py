import os
import re
import ssl
import json
import logging
import urllib.parse
import urllib.request

from pathlib import Path
from datetime import datetime
from argparse import FileType
from argparse import SUPPRESS
from argparse import ArgumentParser
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

from userAgents import *

RED = '\u001b[31m'
GREEN = '\u001b[32m'
RESET = '\u001b[0m'

""" logger """
LOGGERNAME = Path(__file__).stem
logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(LOGGERNAME)
log.setLevel(logging.INFO)
logging.addLevelName(60, "SUCCESS")


def success(self, message, *args, **kws):
    if self.isEnabledFor(60):
        self._log(60, message, args, **kws)


logging.Logger.success = success
logging.addLevelName(70, "FAILED")


def failed(self, message, *args, **kws):
    if self.isEnabledFor(70):
        self._log(70, message, args, **kws)


logging.Logger.failed = failed

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

def recognize(url):
    i = 1
    users = []
    log.info("Brute Forcing users IDs... (/?author=)") #  /?author=
    try:
        while True:
            with urllib.request.urlopen(f'{url}/?author={i}') as response:
                html = response.read()
                title_pattern = re.compile(r"<title>(.*?)</title>")
                matches = re.findall(title_pattern, str(html))
                if matches:
                    user = str(matches[0]).split()[0]
                    log.success(GREEN + user + RESET)
                    users.append(user)
                    i += 1
    except urllib.error.HTTPError:
        log.success(f"LIST: {users}")
    
    log.info("Querying users... (/wp-json/wp/v2/users)") # /wp-json/wp/v2/users
    with urllib.request.urlopen(f'{url}/wp-json/wp/v2/users') as response:
                html = response.read()
                data = json.loads(html)
                log.debug(f"RAW data: {data}")
                for i in data:
                    log.success(GREEN + i["name"] + RESET)

if __name__ == "__main__":
    """ argument """
    parser = ArgumentParser(usage="python %(prog)s -t http://example.com ")

    target = parser.add_argument_group("arguments")
    parser.add_argument("-r", "--raw", action="store_const", const=logging.DEBUG, help="show RAW data")
    target.add_argument("-t", "--target", dest="url", metavar="", help="url of the target")
    args = parser.parse_args()

    if args.url:
        try:
            recognize(args.url)
        except:
            log.fatal(RED + "Site not vulnerable to this method!" + RESET)