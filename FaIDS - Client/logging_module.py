
def traceback_func():
    try:
        debug_mode = configuration.get("debug_mode", True)
    except:
        debug_mode = True
    if debug_mode == True:
        tb = traceback.format_exc()
        return tb

def get_current_date():
            current_date = datetime.now()
            return current_date.strftime("%Y-%m-%d-server")

def check_for_old_logs():
    for file in os.listdir("logs"):
        file_path = os.path.join("logs", file)
        if os.path.isfile(file_path) and file != f"{get_current_date()}.txt":
            zip_and_move(file, file_path)

def zip_and_move(file_name, log_path):
    old_logs_dir = "logs/old_logs"
    os.makedirs(old_logs_dir, exist_ok=True)  # Ensure the 'old_logs' folder exists

    zip_path = os.path.join(old_logs_dir, f"{file_name}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(log_path, arcname=file_name)  # Add the file to the zip with its original name

    os.remove(log_path)  # Delete the original file

def write_log_to_file(logged_message):
        os.makedirs("logs", exist_ok=True)

        # Check for old logs before writing new logs
        check_for_old_logs()

        # Write the log message to today's log file
        log_name = get_current_date()
        try:
            with open(f"logs/{log_name}.txt", "a") as file_log:
                file_log.write(f"{logged_message}\n")
        except Exception as error:
            print(f"ERROR-M-L0-WLTF-01-01: Unexpected error: {error}")
            print("Unexpected error on writing log to file.")
            traceback_func()

def get_current_date_time():
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d %H:%M:%S") 

def log(message, opcode=3):
    """
    Logs given message with date and time, with error code.

    Args:
        message: The message we want to display.
        opcode (int): The message level, of what urgency is the message, defaults to INFO

    Opcodes:
        1 - ERROR
        2 - WARNING
        3 - INFO
        4 - DEBUG

    Raises:
        ConnectionError: If the connection is closed before all data is received.
    """
    opcodes = [None,"ERROR", "WARNING", "INFO", "DEBUG"]
    color_codes = [None, colorama.Fore.RED, colorama.Fore.YELLOW, colorama.Fore.WHITE, colorama.Fore.MAGENTA]
    message_to_log = f"[{get_current_date_time()}] [{opcodes[opcode]}]: {message}"
    message_to_log_colored = f"{color_codes[opcode]}[{get_current_date_time()}] [{opcodes[opcode]}]: {message}{colorama.Fore.WHITE}"
    print(message_to_log_colored)
    write_log_to_file(message_to_log)
    if opcode in [4]:
        tb = traceback_func()
        if not tb or tb is None or "None" in tb:
            return
        trace_back_message = f"{color_codes[opcode]}[{get_current_date_time()}] [{opcodes[opcode]}]: {tb}{colorama.Fore.WHITE}"
        print()
        print(trace_back_message)
        write_log_to_file(trace_back_message)

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

import os
import zipfile
import traceback
import colorama
import platform
from datetime import datetime
from FaIDS import configuration