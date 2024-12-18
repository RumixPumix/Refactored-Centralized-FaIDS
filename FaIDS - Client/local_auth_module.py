import json
import os

def register_user():
    clear_console()
    try:
        username = input("Username: ")
        password = input("Password: ")
        credentials = [username, password]
        if set_credentials(credentials):
            print("Registered successfully!")
            input()
            local_auth()
        else:
            print("Failed to register!")
            input()
            exit()
    except ValueError:
        log("Incorrect input, try again.", 2)
        register_user()
    except Exception as general_error:
        log(f"F-RU-00-01-01 Error: {general_error}", 4)
        log(f"Unknown error occured", 1)
        exit()

def set_credentials(credentials):
    try:
        with open("credentials/user_creds.json", "w") as user_creds_file:
            json.dump(credentials, user_creds_file)
        return True
    except Exception as error:
        log(f"F-SC-00-01-01 Error: {error}", 4)
        log("Error setting credentials", 1)

def retrieve_credentials():
    try:
        with open("credentials/user_creds.json", "r") as user_creds_file:
            user_creds = json.load(user_creds_file)
            username = user_creds[0]
            password = user_creds[1]
            return username, password
    except Exception as error:
        log(f"F-RC-00-01-01 Error: {error}", 4)
        log("Error retrieving credentials", 1)

def get_current_user():
    os.makedirs("credentials", exist_ok=True)
    if not os.path.exists("credentials/user_creds.json"):
        register_user()
    else:
        return retrieve_credentials()

def local_auth():
    clear_console()
    username, password = get_current_user()
    print(f"Welcome {username}, do you wish to continue as this user?")
    try:
        if input("Continue Y/N: ").lower() == "y":
            return(username, password)
        else:
            register_user()
    except ValueError:
        local_auth()
    except Exception as general_error:
        log(f"F-LA-00-01-01 Error: {general_error}", 4)
        log(f"Unknown error occured", 1)
        exit()

from logging import log, clear_console