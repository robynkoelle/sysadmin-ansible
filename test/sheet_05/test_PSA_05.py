import subprocess

def list_postgres_databases():
    cmd = 'sudo -u postgres psql -c "\l"'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def list_postgres_user():
    cmd = 'sudo -u postgres psql -c "\du"'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def print_postgres_hba_file():
    cmd = 'cat /etc/postgresql/16/main/pg_hba.conf'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

# Test if early_bird_user, team02_user, and synapse_user exist in the users and hba file, and if early_bird, team02, synapse exist in the databases.
def test_postgres_users_and_databases():
    users_output = list_postgres_user()
    hba_output = print_postgres_hba_file()
    databases_output = list_postgres_databases()

    # Check if users exist in the list of users
    if 'early_bird_user' in users_output:
        print("early_bird_user exists in the list of users.")
    else:
        print("early_bird_user does not exist in the list of users.")
    
    if 'team02_user' in users_output:
        print("team02_user exists in the list of users.")
    else:
        print("team02_user does not exist in the list of users.")
    
    if 'synapse_user' in users_output:
        print("synapse_user exists in the list of users.")
    else:
        print("synapse_user does not exist in the list of users.")
    
    # Check if users exist in the pg_hba.conf file and print the specific lines
    hba_lines = hba_output.splitlines()
    
    for user in ['early_bird_user', 'team02_user', 'synapse_user']:
        found = False
        for line in hba_lines:
            if user in line:
                print(f"HBA {user}: {line}")
                found = True
                break
        if not found:
            print(f"{user} not found in pg_hba.conf.")

    # Check if databases exist
    if 'early_bird' in databases_output:
        print("early_bird database exists.")
    else:
        print("early_bird database does not exist.")
    
    if 'team02' in databases_output:
        print("team02 database exists.")
    else:
        print("team02 database does not exist.")
    
    if 'synapse' in databases_output:
        print("synapse database exists.")
    else:
        print("synapse database does not exist.")

test_postgres_users_and_databases()
