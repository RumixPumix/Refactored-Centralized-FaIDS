import socket
import threading
import ssl
from logging_module import log
from client_authentication import authenticate_client
from user_credentials_module import get_user_credentials
from main_client_handler import handle_client



def server_listener_main(configuration, key_path, cert_path):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((configuration["server_bind_address"], int(configuration["server_port"])))
            server_sock.listen(5)
            log(f"Server started, listening on: {configuration["server_bind_address"]}:{configuration["server_port"]}", 3)
            with context.wrap_socket(server_sock, server_side=True) as secure_server_sock:
                while True:
                    try:
                        client_connection, client_addr_port = secure_server_sock.accept()
                        log(f"Connection from {client_addr_port}", 3)
                        user_credentials = get_user_credentials()
                        if not user_credentials:
                            log("User credentials not found. Closing server.", 1)
                            secure_server_sock.close()
                            raise SystemExit
                        username = authenticate_client(client_connection, client_addr_port, user_credentials)
                        if username:
                            log(f"Client {username} - {client_addr_port[0]}:{client_addr_port[1]} authenticated successfully.", 3)
                            client_thread = threading.Thread(
                                target=handle_client, 
                                args=(username, client_connection, client_addr_port), 
                                name=f"Client-{username}-{client_addr_port[0]}:{client_addr_port[1]}"
                                )
                            client_thread.daemon = True
                            client_thread.start()
                        else:
                            log(f"Failed authentication for client {client_addr_port[0]}. Connection closed.", 1)
                            client_connection.close()
                            continue
                    
                    except ConnectionResetError as connection_reset_error:
                        log(f"SL-SLM-00-02-01 Client connection reset: {connection_reset_error}", 4)
                        log("The client abruptly disconnected during communication.", 1)
                    except ssl.SSLError as ssl_error:
                        log(f"SL-SLM-00-02-02 SSL error: {ssl_error}", 4)
                        log("An issue occurred while setting up the secure socket with client.", 1)
                    except Exception as error:
                        log(f"SL-SLM-00-02-03 Error: {error}", 4)
                        log("Unexpected error on server listener.", 1)
                    finally:
                        log(f"Closing connection from {client_addr_port}", 3)
                        client_connection.close()
                        continue
    except ssl.SSLError as ssl_error:
        log(f"SL-SLM-00-01-01 SSL error: {ssl_error}", 4)
        log("An issue occurred while setting up the secure socket.", 1)
    except Exception as error:
        log(f"SL-SLM-00-01-01 Error: {error}", 4)
        log("Unexpected error on creating socket.", 1)
    finally:
        log("Server shutting down.", 3)
        server_sock.close()
        log("Server closed.", 3)
        raise SystemExit