from configuration_module import configuration_handler
from certificate_module import certificate_handler
from server_listener import server_listener_main

configuration = {}

if __name__ == "__main__":
    configuration = configuration_handler()
    try:
        key_path, cert_path = certificate_handler()
    except ValueError as error:
        input("Press Enter to exit...")
        exit()
    try:
        server_listener_main(configuration, key_path, cert_path)
    except Exception as error:
        input("Press Enter to exit...")
        exit()