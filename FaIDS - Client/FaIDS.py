from configuration_module import configuration_handler
from logging_module import log, clear_console
from local_auth_module import local_auth
from server_authentication_module import remote_auth
from main_menu_module import main_menu

if __name__ == "__main__":
    configuration = configuration_handler()
    if configuration:
        log("Configuration loaded successfully...", 3)
        username, password = local_auth()
        ssl_socket = remote_auth(username, password, configuration)
        main_menu(ssl_socket, username, configuration)
    else:
        log("Configuration wasn't retrieved...", 3)
        input()
        exit()



