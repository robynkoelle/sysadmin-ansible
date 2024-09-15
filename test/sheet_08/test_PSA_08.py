import subprocess
from ldap3 import Server, Connection, ANONYMOUS, ALL

def print_nsswitch_conf():
    try:
        # Read and print the contents of /etc/nsswitch.conf
        with open('/etc/nsswitch.conf', 'r') as file:
            print("\nContents of /etc/nsswitch.conf:")
            nsswitch_conf = file.read()
            print(nsswitch_conf)

            # Check if sssd is mentioned in nsswitch.conf
            if 'sss' in nsswitch_conf:
                print("\nSSSD is configured in /etc/nsswitch.conf.")
            else:
                print("\nSSSD is not configured in /etc/nsswitch.conf.")
    except FileNotFoundError:
        print("/etc/nsswitch.conf file not found.")
    except Exception as e:
        print(f"An error occurred while reading /etc/nsswitch.conf: {e}")

def check_ldap_anonymous_access(ldap_server_url):
    try:
        # Define the server
        server = Server(ldap_server_url, get_info=ALL)

        # Try to connect anonymously
        conn = Connection(server, authentication=ANONYMOUS)
        if conn.bind():
            print("Connected to LDAP anonymously.")
            conn.unbind()  # Unbind after checking connection
            return True
        else:
            print("Failed to connect to LDAP anonymously.")
            return False
    except Exception as e:
        print(f"An error occurred during LDAP connection: {e}")
        return False

def check_users_in_slapcat():
    # List of users to check
    users_to_check = [
        "humanuser", "mailuser", "psa", "team01", "team02", "team03", "team04", "team05", 
        "team06", "team07", "team08", "team09", "team10", "damian.schneider", "rene.jung", 
        "robyn.koelle", "adrian.averwald", "dominic.fettich", "marco.lutz", "matthias.staritz", 
        "keynan.salmanov", "rouven.rischert", "niklas.brodnicke", "daniel.jerabek", 
        "alexander.petrovski", "lukas.santos", "jakob.steininger", "lea.hartmann", 
        "adele.yessenkulova", "carl.neumann", "lukas.eckert", "miyu.kitamura", "boyong.wu", 
        "Michael Rimmelspacher", "Paulo Seidewitz", "Charlotte Hegenbartova", "Sara Brueckner", 
        "Anatol Schrammel", "Jan Traykov", "Nora Wang", "Lukas Georgiev", "Ferdinand Shulman", 
        "Moritz Engeser", "Ju Feng", "Helma Wittenburg", "Gueney Riedrich", "Philipp Pluda", 
        "Florian Anton Braun", "Yvonne Ottinger", "Robin Wiesner", "Daniel Heusler", 
        "Yue Cebulla", "Sebastian Mittermeier", "Hardik Pfeffer", "Clarissa Attenberger", 
        "Janis von Grotz", "Christian Zinsl", "Nils Koch", "Nicholas Verikios", "Florian Sievers", 
        "Dominic Mehnert", "Simon Brandl", "Jingjing Fischer", "Alexandra Heinz", 
        "Michael Schmolke", "Markus Cato", "Thomas Dominik Popeea", "Johannes Michael Navarrete", 
        "Christoph Beck", "Lisa Liu", "Chi Cuong Lindlacher", "Thomas Becker", "Irina Weinbrenner", 
        "Anja Christina Tran", "Alin Dobrota", "Olga Root", "Peter Heller", 
        "Michael Albert Georg Goel", "Manuel Ruediger", "Nina Klein", "Carina Huber", 
        "Tugba Steinbach", "Christopher Wucherer", "Tobias Treml", "Maksim Herzig", 
        "Andreas Styn", "Rahila Schmidt-Nicic", "Christina Cruz", "Joachim Kent", 
        "Stefan Facher", "Liani Manov", "Thomas Hany", "Florian Markus Holste", 
        "Sebastian Fuchs", "Tobias Hausner", "Stefan Peter Rempe", "Moritz Wolfgang Schlosser", 
        "Ursula Moeller", "Isaac Lean Yi Lang", "Bjorn Kollosche", "Wolfgang Voss", 
        "Liliya Bader", "Sarbani Kilic", "Susanne Yordanov", "Quirin Erdoenmez", 
        "Fabian Matthias Sandmeir", "Van Khiem Maier", "Miroslav Cito", "Alexander Jiang", 
        "Van Manh Hung Loehr", "Jennifer Schlemminger", "Majid Perro", "Jens Hallmann", 
        "Mehmet Can Finis", "Benjamin Marco Murat", "Andreas Schneider", "Florian Barzali", 
        "Moissej Kaushik", "Hoda Olsson", "Andreas Karsunke"
    ]

    try:
        # Run slapcat command and capture its output
        result = subprocess.run(['slapcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if slapcat returned an error
        if result.returncode != 0:
            print(f"Error running slapcat: {result.stderr}")
            return
        
        # Capture the slapcat output
        slapcat_output = result.stdout

        # Count found users
        found_count = 0
        for user in users_to_check:
            if f"cn: {user}" in slapcat_output:
                found_count += 1

        total_users = len(users_to_check)
        
        # Display summary result
        if found_count == total_users:
            print(f"All {found_count} of {total_users} users exist in the slapcat output.")
        else:
            print(f"{found_count} of {total_users} users exist in the slapcat output.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
ldap_server_url = "ldap://localhost"  # Replace with your actual LDAP server URL

# Step 1: Print nsswitch.conf and check if sssd is used
print_nsswitch_conf()

# Step 2: Check if users are in the slapcat output
check_users_in_slapcat()

# Step 3: Check LDAP anonymous access
check_ldap_anonymous_access(ldap_server_url)
