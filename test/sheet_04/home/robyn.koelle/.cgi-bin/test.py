#!/usr/bin/python3

import getpass


def print_http_response():
    username = getpass.getuser()
    response = f"HTTP/1.1 200 OK\nContent-Type: text/plain\n\nHello from cgi script! Running as user {username}"
    print(response)

print_http_response()
