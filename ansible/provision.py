#!/opt/homebrew/bin/python3

import os

tags = input("tags: ")
skip_tags = input("skip-tags: ")
limit = input("limit: ")

command = f"ansible-playbook -i inventory/hosts provision.yml --diff --vault-password-file .vault-key --tags {tags} {'--skip-tags ' + skip_tags if skip_tags else ''} {'-l ' + limit if limit else ''}"

print(command)
os.system(command)

