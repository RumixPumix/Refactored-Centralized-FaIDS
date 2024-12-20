import threading
from client_communication_helper import send_to_client, receive_from_client, transfer_file
from logging_module import log

users_ready_for_file_transfer = {}
users_ready_for_file_transfer_lock = threading.Lock()

authenticated_users = {}
authenticated_users_lock = threading.Lock()

def file_sending_action_handler(client_socket, client_request, client_username):
    match client_request["sub-action"]:
        case 1:
            log(f"Client {client_username} requested users ready for file transfer.", 4)
            with users_ready_for_file_transfer_lock:
                username_list = list(users_ready_for_file_transfer.keys())
            if send_to_client(client_socket, 1, 1, username_list):
                log(f"Sent users ready for file transfer to {client_username}.", 4)
            else:
                log(f"Failed to send users ready for file transfer to {client_username}.", 2)
        case 2:
            client_data = client_request["data"]
            if not client_data:
                log(f"Client {client_username} sent an empty request.", 2)
                return
            try:
                client_username_client_sent, target_username, file_name = client_data
            except ValueError:
                log(f"Client {client_username} sent an invalid request.", 2)
                return
            if client_username_client_sent != client_username:
                log(f"Client {client_username} sent an invalid username.", 2)
                return
            with users_ready_for_file_transfer_lock:
                if target_username not in users_ready_for_file_transfer:
                    log(f"Client {client_username} sent an invalid username to send file to.", 2)
                    return
                target_socket = users_ready_for_file_transfer[target_username][0]
                if not target_socket:
                    log(f"Couldn't extract socket object for username: {target_username}", 1)
                    return
                request_data = {"from_user": client_username, "file_name": file_name}
                if not send_to_client(target_socket, 2, 2, request_data):
                    log(f"Failed to send file sending request to {target_username}.", 2)
                    return
                target_client_response = receive_from_client(target_socket)
                if not target_client_response:
                    log(f"Failed to receive response from {target_username}.", 2)
                    return
                if target_client_response == True:
                    if not send_to_client(client_socket, 1, 3, True):
                        log(f"Failed to send file sending confirmation to {client_username}.", 2)
                        return
                    log(f"Initiating file transfer from {client_username} to {target_username}.", 4)
                    transfer_file(client_socket, target_socket)
                else:
                    log(f"Failed to initiate file transfer from {client_username} to {target_username}.", 2)
                    return
                #TU TREBA POSLAT SENDER DA JE SVE OK I DA SALJE FILE.
        case 3:
            if client_username in users_ready_for_file_transfer:
                file_sending_socket = users_ready_for_file_transfer[client_username]
                file_sending_socket.sendall(b"File sending starting...")
                log(f"File sending starting to {client_username}.", 4)
            else:
                log(f"Client {client_username} not ready for file transfer.", 4)
        case None:
            log(f"Client {client_username} sent an invalid sub-action.", 2)
            return
    return

def file_receiving_action_handler(client_socket, client_request, client_username):
    match client_request["sub-action"]:
        case 1:
            with users_ready_for_file_transfer_lock:
                users_ready_for_file_transfer[client_username] = client_socket
            log(f"Client {client_username} is ready for file transfer.", 4)
        case 2:
            with users_ready_for_file_transfer_lock:
                if client_username in users_ready_for_file_transfer:
                    del users_ready_for_file_transfer[client_username]
            log(f"Client {client_username} is no longer ready for file transfer.", 4)
        case 3:
            log(f"Client {client_username} {client_request["data"]} file sending request.", 4)
        case None:
            log(f"Client {client_username} sent an invalid sub-action.", 2)
            return
    return

def handle_client(client_username, client_socket, client_addr_port):
    with authenticated_users_lock:
        authenticated_users[client_username] = [client_socket, client_addr_port]
    while True:
        try:
            client_request = receive_from_client(client_socket, False)
            if client_request is None:
                break
            match client_request["action"]:
                case 1:
                    file_sending_action_handler(client_socket, client_request, client_username)
                case 2:
                    file_receiving_action_handler(client_socket, client_request, client_username)
                case None:
                    break
        except (ConnectionResetError, ConnectionAbortedError):
            client_socket.close()
            with authenticated_users_lock:
                del authenticated_users[client_username]
            log(f"Client {client_username} abruptly disconnected.", 2)
            return
    client_socket.close()
    with authenticated_users_lock:
        del authenticated_users[client_username]
    log(f"Client {client_username} disconnected.", 3)
    return

