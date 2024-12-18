from client_communication_helper import send_to_client, receive_from_client
from logging_module import log

def authenticate_client(client_socket, client_addr_port, user_credentials):

    client_response_credentials = receive_from_client(client_socket)
    if not client_response_credentials:
        log(f"Failed authentication for client {client_addr_port[0]}:{client_addr_port[1]}.", 4)
        return False
    try:
        client_username, client_password = client_response_credentials
    except ValueError:
        log(f"Failed authentication for client {client_addr_port[0]}:{client_addr_port[1]}.", 4)
        send_to_client(client_socket, 0,0,False)
        return False
    if client_username in user_credentials and user_credentials[client_username] == client_password:
        send_to_client(client_socket, 0,0,True)
        return client_username
    else:
        log(f"Failed authentication for client {client_addr_port[0]}:{client_addr_port[1]}. Login info: {client_username}:{client_password}", 4)
        send_to_client(client_socket, 0,0,False)
        return False