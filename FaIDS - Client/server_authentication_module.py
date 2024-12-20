import socket
from server_communication_helper_func import remote_authentication
from logging_module import log
import ssl

def parse_configuration(config):
    server_ip = config.get("server_ip_address", None)
    if server_ip == None:
        log("No server IP to connect to!", 2)
        input("Exiting...")
        exit()
    server_port = config.get("server_port", None)
    if server_port == None:
        log("No server port to connect to!", 2)
        input("Exiting...")
        exit()
    return server_ip, server_port

def remote_auth(username, password, configuration):
    server_ip, server_port = parse_configuration(configuration)
    try:
        log(f"Connecting to server at {server_ip}:{server_port}...", 3)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        socket_stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_stream.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            socket_stream.connect((server_ip, server_port))
        except TimeoutError:
            log("Server didn't respond...", 2)
            return None
        log(f"Successfully connected at {server_ip}:{server_port}.", 3)
        ssl_client_connection = context.wrap_socket(socket_stream, server_hostname=server_ip)
        log("Logging in...", 3)
        server_authentication_response = remote_authentication(ssl_client_connection, username, password)
        if server_authentication_response == None:
                log("Server didn't respond...", 2)
                return None
        if server_authentication_response == False:
                log("Incorrect login info!", 2)
                return None
        log("Successfully authenticated with server!", 3)
        return ssl_client_connection
    except Exception as general_error:
        log(f"SCM-RA-00-01-01 Error: {general_error}", 4)
        log(f"Error creating secure socket to connect to server!", 1)
        ssl_client_connection.close()
        return None