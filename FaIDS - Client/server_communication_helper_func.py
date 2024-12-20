import json
import os
import time
import ssl
from logging_module import log, clear_console
from chunk_size_calculator import get_optimal_chunk_size

import ssl

def is_socket_active(socket_obj):
    try:
        # Check if the socket is an instance of ssl.SSLSocket and if it's still open
        return socket_obj.fileno() != -1
    except Exception as e:
        # If an error occurs, the socket might be invalid
        log(f"Error checking socket: {e}", 1)
        return False

def send_to_server(socket_obj, action, sub_action, data):
    if not is_socket_active(socket_obj):
        log("Connection to the server was lost!", 1)
        return None
    """
    Sends a structured message to the server.

    Args:
        socket_obj: The socket_obj object used to send data.
        action (str): The main action for the request.
        sub_action (str): The sub-action for the request.
        data (dict): The payload to include in the request.

    Returns:
        bool: True if the data was sent successfully, False otherwise.

    Structure:
        action:
            1 - File Sending
                sub-action:
                    1 - Get active users ready for file transfer from server.
                    2 - Send request to user for file transfer.
                    3 - File sending starting...
            2 - File Receiving
                sub-action:
                    1 - Set client state to 'ready for file transfer'.
                    2 - Accept file sending request.
                    3 - Decline file sending request.
            3 - Domain Requests
            4 - Authentication
                sub-action:
                    0 - Send credentials to log in.

    """
    log("Preparing data for sending to server...", 4)

    # Format the data into a dictionary
    formatted_data = {
        "action": action,
        "sub-action": sub_action,
        "data": data
    }
    log(f"Formatted data: {formatted_data}", 4)

    # Serialize the data to JSON format
    log("Serializing the data...", 4)
    try:
        serialized_data = json.dumps(formatted_data).encode()  # Convert to bytes
        serialized_data_len = len(serialized_data).to_bytes(4, 'big')  # Add 4-byte length
    except Exception as serialization_error:
        log(f"SCHF-STS-00-01-01 Error: {serialization_error}", 4)
        log("Error serializing data...", 1)
        return False

    # Send the data over the socket_obj
    try:
        log("Sending the serialized data length via socket_obj...", 4)
        socket_obj.sendall(serialized_data_len)
        log("Sending the serialized data via socket_obj...", 4)
        socket_obj.sendall(serialized_data)
        log("Data sent successfully to server.", 4)
        return True
    except (BrokenPipeError, ConnectionError):
        log("SCHF-STS-00-02-02 Error: socket_obj connection broken (BrokenPipeError).", 1)
    except OSError as os_error:
        log(f"SCHF-STS-00-02-03 Error: {os_error}", 1)
    except Exception as general_error:
        log(f"SCHF-STS-00-02-01 Error: {general_error}", 1)
        log("Error sending data to server...", 1)
    
    return None

def receive_from_server(socket_obj, extracted=True):
    if not is_socket_active(socket_obj):
        log("Connection to the server was lost!", 1)
        return None
    """
    Receives and deserializes data from the server.

    Args:
        socket_obj: The socket_obj object to receive data from.

    Returns:
        dict: The deserialized data if successful.
        None: If any error occurs.
    """
    log("Preparing to receive data from server...", 4)
    try:
        # Receive the length of the incoming data
        serialized_data_len_bytes = socket_obj.recv(4)
        if not serialized_data_len_bytes:
            log("No data received from server (connection may be closed).", 1)
            #socket_obj.close()  # Gracefully close the socket_obj
            return None

        serialized_data_len = int.from_bytes(serialized_data_len_bytes, 'big')
        log(f"Expected data length: {serialized_data_len} bytes", 4)

        # Receive the complete data
        received_data = recv_all(socket_obj, serialized_data_len)
        log(f"Received: {len(received_data)} bytes from server.", 4)

        # Deserialize the JSON data
        log("Deserializing the data...", 4)
        try:
            deserialized_data = json.loads(received_data.decode())
            log(f"Deserialized data: {deserialized_data}", 4)
            if extracted:
                return extract_data_from_server_response(deserialized_data)
            return deserialized_data
        except json.JSONDecodeError as json_error:
            log(f"SCHF-RFS-00-01-01 Error: {json_error}", 4)
            log("Error deserializing data from server...", 1)
            return None
    except Exception as general_error:
        log(f"SCHF-RFS-00-02-01 Error: {general_error}", 4)
        log("Error receiving data from server...", 1)
        return None


def recv_all(socket_obj, length):
    """
    Receives an exact amount of data from the socket_obj.

    Args:
        socket_obj: The socket_obj object to receive data from.
        length (int): The number of bytes to receive.

    Returns:
        bytes: The received data.

    Raises:
        ConnectionError: If the connection is closed before all data is received.
    """
    data = b""
    while len(data) < length:
        packet = socket_obj.recv(length - len(data))
        if not packet:
            log("Connection closed prematurely. When recv_all func is called.", 1)
            raise ConnectionError("Socket connection closed prematurely")
        data += packet
    return data

def extract_data_from_server_response(server_response):
    try:
        data = server_response.get("data", False)
        return data
    except Exception as general_error:
        log(f"SCHF-EDFSR-00-01-01 Error: {general_error}", 4)
        return False

def calculate_download_speed(received, filesize, start_time):
    elapsed_time = time.time() - start_time
    if elapsed_time > 0:
        speed_in_mb = (received / (1024 * 1024)) / elapsed_time  # Speed in MB/s
        speed_in_kb = (received / 1024) / elapsed_time  # Speed in KB/s
    clear_console()
    # Determine if the file size should be displayed in KB or MB
    if filesize < 1024 * 1024:  # Less than 1 MB
        if 0.1 <= speed_in_mb <= 0.9:
            log(f"Downloaded {received / 1024:.2f} KB of {filesize / 1024:.2f} KB "
                f"at {speed_in_kb:.2f} KB/s", 3)
        else:
            log(f"Downloaded {received / 1024:.2f} KB of {filesize / 1024:.2f} KB "
                f"at {speed_in_mb:.2f} MB/s", 3)
    else:  # 1 MB or more
        if 0.1 <= speed_in_mb <= 0.9:
            log(f"Downloaded {received / (1024 * 1024):.2f} MB of {filesize / (1024 * 1024):.2f} MB "
                f"at {speed_in_kb:.2f} KB/s", 3)
        else:
            log(f"Downloaded {received / (1024 * 1024):.2f} MB of {filesize / (1024 * 1024):.2f} MB "
                f"at {speed_in_mb:.2f} MB/s", 3)




###PREDEFINED FUNCTIONS

def get_current_file_transfer_ready_users(socket_obj, username):
    if send_to_server(socket_obj,1,1,username): #On server side, make checks which equate to verifying if the user is acctually who he says he is.
        log("Sent request successfully...", 4)
        list_of_users = receive_from_server(socket_obj)
        if list_of_users:
            if list_of_users == False:
                log("No key matching 'data' was found in server's response!", 4)
                return None
            else:
                log("Received a list of file transfer ready users!", 4)
            return list_of_users
        else:
            log("Failed to receive response from server!", 4)
            return None
    else:       
        log("Failed to send request to the server!", 4)
        return None

def send_request_to_user(socket_obj, username, file_to_send, target):
    if send_to_server(socket_obj,1,2,[username, target, file_to_send]):
        server_response = receive_from_server(socket_obj)
        if not server_response:
            log("Failed to receive response from server!", 4)
            return None
        if server_response:
            log("Received response from server, True", 4)
            return True
        else:
            log("Received response from server, False", 4)
            return False
    else:
        log("Failed to send request to the server!", 4)
        return None

def receive_request_from_user(socket_obj, username):
    if send_to_server(socket_obj, 2, 1, username): #On server side, make checks which equate to verifying if the user is acctually who he says he is.
        log("Sent request successfully...", 4)
    else:
        log("Failed to send request to the server!", 4)
        return None

    file_request_server_response = receive_from_server(socket_obj)
    if file_request_server_response: 
        log("Received request from user...", 4)
        from_user_username = file_request_server_response.get("from_user", False)
        file_to_receive = file_request_server_response.get("file_name", False)
        if not from_user_username or not file_to_receive:
            log("Received request from user, but couldn't extract data!", 4)
            return None
        return [from_user_username, file_to_receive]
    else:
        log("Failed to receive request from user!", 4)
        return None
        

def send_file_to_user(socket_obj, filename):
    filepath = f"files/send/{filename}"
    if not os.path.isfile(filepath):
        log(f"File does not exist: {filepath}", 4)
        return False
    try:
        filesize = os.path.getsize(filepath)
    except OSError as os_error:
        log(f"SCHF-SFTU-00-01-01 Error: {os_error}", 4)
        return False
    
    file_metadata = {"filename": filename, "filesize": filesize}
    response = send_to_server(socket_obj, 1, 3, file_metadata)
    if not response:
        return response
    
    chunk_size = get_optimal_chunk_size(filesize)

    log(f"Sending file: {filename}, ({filesize} bytes) in chunks of {chunk_size} bytes", 4)

    try:
        with open(filepath, "rb") as file:
            while (chunk := file.read(chunk_size)):
                socket_obj.sendall(chunk)
    except (OSError, IOError, ConnectionError) as socket_obj_error:
        log(f"SCHF-SFTU-00-02-01 Error: {socket_obj_error}", 4)
        return None
    return True

def receive_file_from_user(socket_obj):
    if not send_to_server(socket_obj,2,2, None):
        log("Failed to send response to server!", 4)
        return None
    
    file_metadata = receive_from_server(socket_obj)

    filename = file_metadata.get("filename", False)
    filesize = file_metadata.get("filesize", False)

    chunk_size = get_optimal_chunk_size(filesize)
    log(f"Receiving file: {filename}, ({filesize} bytes) in chunks of {chunk_size} bytes", 3)

    try:
        os.makedirs("files/receive", exist_ok=True)
    except OSError as os_error:
        log(f"SCHF-RFFU-00-01-01 Error: {os_error}", 4)
        return False

    filepath = os.path.join("files/receive", filename)
    try:
        with open(filepath, "wb") as file:
            received = 0
            start_time = time.time()  # Start timing
            while received < filesize:
                try:
                    data = socket_obj.recv(min(chunk_size, filesize - received))
                except ConnectionError as connection_error:
                    log(f"SCHF-RFFU-00-03-01 Error: {connection_error}", 4)
                    return None
                if not data:
                    log("Connection lost during file transfer.", 4)
                    return None
                file.write(data)
                received += len(data)
                calculate_download_speed(received, filesize, start_time)
    except (OSError, IOError) as os_io_error:
        log(f"SCHF-RFFU-00-02-01 Error: {os_io_error}", 4)
        return False

    log("File transfer complete.", 4)
    return True

def remote_authentication(socket_obj, username, password):
    if send_to_server(socket_obj,4,0,[username, password]):
        server_response = receive_from_server(socket_obj)
        if server_response is None:
            log("Failed to receive response from server!", 4)
            return None
        if server_response:
            log("Received response from server, Authentication successful", 4)
            return True
        else:
            log("Received response from server, Authentication failed", 4)
            return False
    else:
        log("Failed to send request to the server!", 4)
        return None
