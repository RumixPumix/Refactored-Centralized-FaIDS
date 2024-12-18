import os
import json
from logging_module import log

def get_user_credentials():
        os.makedirs("credentials", exist_ok=True)
        try:
            if not os.path.exists("credentials/users_creds.json"):
                with open("credentials/users_creds.json", "w") as user_cred_file:
                    default_creds = {"admin": "Pa$$w0rd"}
                    log("Default credentials set: admin - Pa$$w0rd", 3)
                    json.dump(default_creds, user_cred_file)
            with open("credentials/users_creds.json", "r") as user_cred_file:
                return json.load(user_cred_file)
        except PermissionError as perm_error:
            log(f"UCM-GUC-00-01-01 Permission error: {perm_error}", 4)
            log("Unable to write to the credentials file due to insufficient permissions.", 1)
        except OSError as os_error:
            log(f"UCM-GUC-00-01-02 OS error: {os_error}", 4)
            log("Failed to create or write to the credentials file due to a system issue.", 1)
        except Exception as error:
            log(f"UCM-GUC-00-01-03 Error: {error}", 4)
            log("Unexpected error on loading credentials!", 1)
        return False