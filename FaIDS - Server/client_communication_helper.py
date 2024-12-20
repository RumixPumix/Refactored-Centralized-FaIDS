from logging_module import log, clear_console
from chunk_size_calculator import get_optimal_chunk_size
import json

#Core functions

def is_socket_active(socket_obj):
    try:
        # Check if the socket is an instance of ssl.SSLSocket and if it's still open
        return socket_obj.fileno() != -1
    except Exception as e:
        # If an error occurs, the socket might be invalid
        log(f"Error checking socket: {e}", 1)
        return False

def send_to_client(socket, action, sub_action, data):
    if not is_socket_active(socket):
        log("Connection to the server was lost!", 1)
        return None
    """
    Sends a structured message to the client.

    Args:
        socket: The socket object used to send data.
        action (str): The main action for the request.
        sub_action (str): The sub-action for the request.
        data (dict): The payload to include in the request.

    Returns:
        bool: True if the data was sent successfully, False otherwise.

    Structure:
        action:
            1 - File Sending
             sub-action:
                1 - Get active users ready for file transfer from client.
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
    log("Preparing data for sending to client...", 4)

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
        log(f"CCH-STC-00-01-01 Error: {serialization_error}", 4)
        log("Error serializing data...", 1)
        return False

    # Send the data over the socket
    try:
        log("Sending the serialized data length via socket...", 4)
        socket.sendall(serialized_data_len)
        log("Sending the serialized data via socket...", 4)
        socket.sendall(serialized_data)
        log("Data sent successfully to client.", 4)
        return True
    except (BrokenPipeError, ConnectionError):
        log("CCH-STC-00-02-02 Error: Socket connection broken (BrokenPipeError).", 1)
    except OSError as os_error:
        log(f"CCH-STC-00-02-03 Error: {os_error}", 1)
    except Exception as general_error:
        log(f"CCH-STC-00-02-01 Error: {general_error}", 1)
        log("Error sending data to client...", 1)
    
    return None

def receive_from_client(socket, extracted=True):
    if not is_socket_active(socket):
        log("Connection to the client was lost!", 1)
        return None
    """
    Receives and deserializes data from the client.

    Args:
        socket: The socket object to receive data from.

    Returns:
        dict: The deserialized data if successful.
        None: If any error occurs.
    """
    log("Preparing to receive data from client...", 4)
    try:
        # Receive the length of the incoming data
        serialized_data_len_bytes = socket.recv(4)
        if not serialized_data_len_bytes:
            log("No data received from client (connection may be closed).", 1)
            #socket.close()  # Gracefully close the socket
            return None

        serialized_data_len = int.from_bytes(serialized_data_len_bytes, 'big')
        log(f"Expected data length: {serialized_data_len} bytes", 4)

        # Receive the complete data
        received_data = recv_all(socket, serialized_data_len)
        log(f"Received {len(received_data)} bytes from client.", 4)

        # Deserialize the JSON data
        log("Deserializing the data...", 4)
        try:
            deserialized_data = json.loads(received_data.decode())
            log(f"Deserialized data: {deserialized_data}", 4)
            if extracted:
                return extract_data_from_client_response(deserialized_data)
            return deserialized_data
        except json.JSONDecodeError as json_error:
            log(f"CCH-RFC-00-01-01 Error: {json_error}", 4)
            log("Error deserializing data from client...", 1)
            return None
    except Exception as general_error:
        log(f"CCH-RFC-00-02-01 Error: {general_error}", 4)
        log("Error receiving data from client...", 1)
        return None
    
def recv_all(socket, length):
    """
    Receives an exact amount of data from the socket.

    Args:
        socket: The socket object to receive data from.
        length (int): The number of bytes to receive.

    Returns:
        bytes: The received data.

    Raises:
        ConnectionError: If the connection is closed before all data is received.
    """
    data = b""
    while len(data) < length:
        packet = socket.recv(length - len(data))
        if not packet:
            raise ConnectionError("Socket connection closed prematurely")
        data += packet
    return data

def extract_data_from_client_response(client_response):
    try:
        data = client_response.get("data", False)
        return data
    except Exception as general_error:
        log(f"CCH-EDFSR-00-01-01 Error: {general_error}", 4)
        return False
    
#Predefined functions

def transfer_file(from_socket, to_socket):
    """
    Transfers a file from the sender to the receiver.

    Args:
        receiver_socket: The socket object of the receiver.
        sender_socket: The socket object of the sender.
    """
    log("Initiating file transfer...", 4)

    file_metadata = receive_from_client(from_socket)
    if not file_metadata:
        log("Failed to receive file metadata.", 2)
        return
    filename = file_metadata.get("filename", None)
    filesize = file_metadata.get("filesize", None)
    if not filename or not filesize:
        log("Invalid file metadata received.", 2)
        return
    log(f"Received file metadata: {filename} - {filesize} bytes", 4)
    if send_to_client(to_socket, 2, 1, file_metadata):
        log("File metadata sent successfully.", 4)

    chunk_size = get_optimal_chunk_size(filesize)
    log(f"Starting file transfer: {filename} ({filesize} bytes) in chunks of {chunk_size} bytes", 3)

    transferred = 0
    while transferred < filesize:
        data = from_socket.recv(min(chunk_size, filesize - transferred))
        if not data:
            log("Connection lost during file transfer.", 1)
            break
        to_socket.sendall(data)
        transferred += len(data)

    # Log completion status
    if transferred == filesize:
        log(f"File transfer completed: {filename} ({transferred}/{filesize} bytes)", 3)
    else:
        log(f"File transfer incomplete: {filename} ({transferred}/{filesize} bytes)", 1)