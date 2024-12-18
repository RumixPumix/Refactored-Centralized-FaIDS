from logging_module import clear_console

def list_options_func(list_to_print):
    if not list_to_print:
        return None

    while True:
        # Clear the console if the function exists
        try:
            clear_console()
        except NameError:
            pass

        # Display the options using enumerate
        print("0. Exit")
        for index, item in enumerate(list_to_print, start=1):
            print(f"{index}. {item}")
        
        try:
            # Prompt user input
            selected_index = int(input("Select: "))
            if selected_index == 0:
                return False  # User wants to exit
            elif 1 <= selected_index <= len(list_to_print):
                return list_to_print[selected_index - 1]
            else:
                print("No option with that number!")
        except ValueError:
            print("Invalid input! Please enter a number.")
        input("Press Enter to continue...")
        
       