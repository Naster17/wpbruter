# wpbruter
### Tool for Massive mask and dictionary attacks, auto recognize, proxy, threads and other cool features for Word Press
#### Install:
``` git clone https://github.com/Naster17/wpbruter/ ```
#### Combination cases:
Auto attack users on site using wordlist <br>
``` python main.py --target https://site.com --wpassword rockyou.txt --auto ``` <br>
Tries the password and users on all sites in the list <br>
``` python main.py --wtarget sites.txt --user admin --password admin123 --thread 5``` <br>
Uses user and password dictionaries on one site <br>
``` python main.py --target site.com --wusers users.txt --wpassword passwords.txt ``` <br>
Mass bruteforce <br>
``` python main.py --wtarget sites.txt --wusers users.txt --wpassword passwords.txt ``` <br>

### Cool features:
- Can exploit "Username leakage vulnerability"
- Written in pure Python, no dependencies need to be installed <br>
- Multithreaded
- A large number of attack combinations

### Docs
``` --auto ``` Automatically recognizes available usernames by exploiting vulnerabilities in wp (author leak) 
<br>
``` --cheatsheet ``` Help with mask attacks <br>
```UPPER:         user -> USER
LOWER:         USER -> user
TITLE:         user -> User
REVERSE:       user -> resu
UPPER-REVERSE: user -> RESU
LOWER-REVERSE: USER -> resu
TITLE-REVERSE: user -> resU

MINUS[1-9]:    1: user -> ser
               2: user -> er
               3: user -> r
               ...
```
#### Main param:
``` --target ``` URL to attack site example: https://mysite.com <br>
``` --wtarget ``` wordlist file with list of URLs <br>
``` --mask ``` Mask rule for passwords use --cheatsheet for more info <br>
``` --site-mask ``` Mask rule for site names use --cheatsheet for more info <br>

#### Creds param:
``` --username ``` Static one username example: admin <br>
``` --wusers ``` wordlist with user names <br>
``` --password ``` Static password example: admin123 <br>
``` --wpassword ``` wordlist with passwords <br>

### Other param:
``` --timeout ``` timed out for requests in sec example: 1 <br>
``` --thread ``` numbers of threading example: 4 <br>
``` --proxy ``` example: 127.0.0.1:8080 auto detect proxy type (http, https supports) <br>
``` --proxy-list ``` wordlist with proxy <br>
