#!/usr/bin/python3

import os
import requests
import subprocess
from urllib3.exceptions import InsecureRequestWarning

# Suppress the InsecureRequestWarning from urllib3.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Ensure no proxies are used.
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

GREEN = '\033[92m'  # Green text
RED = '\033[91m'    # Red text
RESET = '\033[0m'   # Reset color

def printc(text, color):
    print(f"{color}{text}{RESET}")


def check_response(url, expectedResponse):
    try:
        session = requests.Session()

        response = requests.get(f"http://{url}", verify=False, allow_redirects=True)

        # Check if final URL is HTTPS.
        if response.url.startswith("https://"):
            printc(f"PASS: {url} correctly redirects to HTTPS.", GREEN)
        else:
            printc(f"FAIL: {url} does not redirect to HTTPS.", RED)

        # Check if accessible via HTTPS directly and returns the correct content
        response_https = requests.get(f"https://{url}", verify=False)
        if response_https.status_code == 200 and expectedResponse in response_https.text:
            printc(f"PASS: HTTPS accessible and correct message returned from {url}.", GREEN)
        else:
            printc(f"FAIL: Problem with HTTPS access or message for {url}. Expected: {expectedResponse}, actual: {response_https.text}", RED)
    except Exception as e:
        printc(f"ERROR: An exception occurred for {url}. Details: {str(e)}", RED)


def run_logrotate_debug(config_file):
    try:
        result = subprocess.run(["logrotate", "-d", config_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        printc(result.stdout)
    except subprocess.CalledProcessError as e:
        printc(f"Error running logrotate: {str(e)}", RED)
        print(e.stderr)
    except FileNotFoundError:
        printc("logrotate is not installed or not found in the system path.", RED)


print("Check early-bird.psa-team02.cit.tum.de ...")
check_response("early-bird.psa-team02.cit.tum.de", "Hello from early-bird!")

print("Check bearly-ird.psa-team02.cit.tum.de ...")
check_response("bearly-ird.psa-team02.cit.tum.de", "Hello from bearly-ird!")

print("Check www.psa-team02.cit.tum.de ...")
check_response("www.psa-team02.cit.tum.de", "Hello from team02!")

print("Check static content of users ...")
check_response("early-bird.psa-team02.cit.tum.de/~robyn.koelle", "Hello from robyn.koelle!")
check_response("early-bird.psa-team02.cit.tum.de/~robyn.koelle/", "Hello from robyn.koelle!")
check_response("early-bird.psa-team02.cit.tum.de/~robyn.koelle/index.html", "Hello from robyn.koelle!")
check_response("early-bird.psa-team02.cit.tum.de/~robyn.koelle/nested/test.html", "Hello from robyn.koelle (nested)!")

print("Check CGI scripts work ...")
check_response("early-bird.psa-team02.cit.tum.de/~robyn.koelle/cgi-bin/test.py", "Hello from cgi script!")

print("Check CGI scripts run as requested user ...")
check_response("early-bird.psa-team02.cit.tum.de/~robyn.koelle/cgi-bin/test.py", "Running as user robyn.koelle")

print("Check nginx log rotation config:")
run_logrotate_debug("/etc/logrotate.d/nginx")
