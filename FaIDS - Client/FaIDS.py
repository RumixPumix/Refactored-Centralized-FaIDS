from configuration_module import configuration_handler
from logging_module import log, clear_console
from local_auth_module import local_auth
from server_authentication_module import remote_auth
from main_menu_module import main_menu

configuration = {}

if __name__ == "__main__":
    configuration = configuration_handler()
    if configuration:
        log("Configuration loaded successfully...", 3)
        authenticated = False
        while not authenticated:
            username, password = local_auth()
            ssl_socket_obj = remote_auth(username, password, configuration)
            if ssl_socket_obj:
                authenticated = True
            else:
                log("Failed to authenticate with server! Please try again.", 1)
        main_menu(ssl_socket_obj, username, configuration)
    else:
        log("Configuration wasn't retrieved...", 3)
        input()
        exit()
    log("Exiting...", 3)
    input()
    exit()


