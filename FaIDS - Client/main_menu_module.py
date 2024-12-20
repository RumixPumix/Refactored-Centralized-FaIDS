import os
from main_menu_helper_func import list_options_func
from server_communication_helper_func import get_current_file_transfer_ready_users, send_file_to_user, send_request_to_user, receive_request_from_user, receive_file_from_user, send_to_server, is_socket_active
from logging_module import log

MAIN_MENU_OPTIONS = ["Send A File", "Receive A File", "Sub-Domain Request"]

def file_sending_menu(socket_obj, username): #Add a refresh option for current users, also add possibility to send it to multiple users!
    selected_file = list_options_func(os.listdir("files/send"))
    if selected_file is None:
        log("No files are placed inside /files/send folder!", 2)
        return
    selected_user = list_options_func(get_current_file_transfer_ready_users(socket_obj, username)) #DODAT OPCIJU "R" KAO REFRESH NA USER LIST.
    if selected_user is None:
        log("Failed to get user list!", 1)
        return
    elif selected_user == False:
        log("No user selected.", 1)
        return

    request_response = send_request_to_user(socket_obj, username, selected_file, selected_user)
    if request_response == True:
        log(f"Recipient {selected_user} accepted, sending file...", 3)
        response = send_file_to_user(socket_obj, username, selected_file, selected_user)
        if response == None:
            log("Couldn't send file due to connection errors!", 1)
        elif response == False:
            log("Couldn't send file due to client-sided errors!", 1)
        else:
            log("File sent successfully!", 3)
    elif request_response == False:
        log("User declined file transfer.", 2)
    else:
        log("No response from user. Failed to contact user.", 1)
    return

def file_receiving_menu(socket_obj, username):
    print(type(socket_obj), "4")
    print("Waiting for incoming file...")
    file_request_message = receive_request_from_user(socket_obj, username)
    if file_request_message is None:
        log("Failed to receive request from user!", 1)
        return
    try:
        from_user, file_name = file_request_message
    except ValueError:
        log("Failed to receive request from user!", 1)
        return
    print(f"User {from_user} wants to send you a file: {file_name}")
    response = list_options_func(["Accept", "Decline"])
    if response == "Accept":
        if not send_to_server(socket_obj,2,3,True):
            log("Failed to send response to server! Recipient didn't get accept message", 4)
            return
        else:
            log("Accepted file transfer.", 3)
        #TU TREBA DODAT DA SE POSALJE "YES" SERVERU DA JE ACCEPTED REQUEST I DA SE POSALJE FILE
        response = receive_file_from_user(socket_obj)
        if response == None:
            log("Failed to receive file due to connection errors!", 1)
        elif response == False:
            log("Failed to receive file due to client-sided errors!", 1)
        else:
            log(f"File received successfully! Located at: 'files/receive/{file_name}'", 3)
    else:
        if send_to_server(socket_obj,2,3,False):
            log("Failed to send response to server! Recipient didn't get decline message", 4)
            return
        else:
            log("Declined file transfer.", 3)
def sub_domain_request_menu():
    pass


def main_menu(socket_obj, username, configuration):
    while True:
        main_menu_index = 1
        for main_menu_option in MAIN_MENU_OPTIONS:
            print(f"{main_menu_index}. {main_menu_option}")
            main_menu_index += 1
        try:
            if not is_socket_active(socket_obj):
                log("Connection to server lost!", 1)
                return
            selected_option = int(input("Option: ")) - 1
            match selected_option:
                case 0:
                    file_sending_menu(socket_obj, username)
                case 1:
                    file_receiving_menu(socket_obj, username)
                case 3:
                    sub_domain_request_menu()
        except ValueError:
            main_menu(socket_obj, username, configuration)
